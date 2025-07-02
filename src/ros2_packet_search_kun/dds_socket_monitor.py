import time
import threading
import socket
import struct
from collections import defaultdict
from datetime import datetime
from typing import Dict, Set, Optional, Tuple, List
import select


class DDSSocketMonitor:
    def __init__(self, report_interval: float = 5.0):
        self.report_interval = report_interval
        self.packet_stats: Dict[str, int] = defaultdict(int)
        self.byte_stats: Dict[str, int] = defaultdict(int)
        self.running = False
        self.stats_lock = threading.Lock()
        
        # DDS multicast addresses and ports
        self.dds_multicast_addresses = [
            "239.255.0.1",  # DDS default multicast address
            "239.255.0.2",
            "239.255.0.3",
        ]
        
        # DDS discovery ports
        self.dds_ports = [7400, 7401, 7402, 7403, 7404, 7405, 7406, 7407, 7408, 7409, 7410, 7411]
        
        self.sockets: List[socket.socket] = []
    
    def create_multicast_socket(self, multicast_addr: str, port: int) -> Optional[socket.socket]:
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to the multicast address and port
            sock.bind(('', port))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(multicast_addr), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Set socket to non-blocking
            sock.setblocking(False)
            
            return sock
        except Exception as e:
            print(f"Failed to create socket for {multicast_addr}:{port} - {e}")
            return None
    
    def setup_sockets(self):
        print("Setting up DDS multicast listeners...")
        
        # Create sockets for each multicast address and port combination
        for addr in self.dds_multicast_addresses:
            for port in self.dds_ports:
                sock = self.create_multicast_socket(addr, port)
                if sock:
                    self.sockets.append(sock)
                    print(f"Listening on {addr}:{port}")
        
        if not self.sockets:
            print("Warning: No sockets could be created. You may not see any DDS traffic.")
        else:
            print(f"Successfully created {len(self.sockets)} multicast listeners")
    
    def is_dds_packet(self, data: bytes) -> bool:
        if len(data) < 4:
            return False
        
        # Check for RTPS header
        if data[:4] == b'RTPS':
            return True
        
        # Check for other DDS/RTPS patterns
        # DDS packets often start with specific protocol identifiers
        if len(data) >= 8:
            # Check for common DDS message patterns
            if data[0:2] in [b'\x52\x54', b'\x44\x44']:  # RT or DD prefixes
                return True
        
        return True  # Assume packets on DDS multicast addresses are DDS packets
    
    def process_packet(self, data: bytes, addr: Tuple[str, int]):
        if self.is_dds_packet(data):
            src_ip = addr[0]
            packet_size = len(data)
            
            with self.stats_lock:
                self.packet_stats[src_ip] += 1
                self.byte_stats[src_ip] += packet_size
    
    def format_bytes(self, bytes_count: int) -> str:
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.1f} KB"
        elif bytes_count < 1024 * 1024 * 1024:
            return f"{bytes_count / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"
    
    def print_stats(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.stats_lock:
            if not self.packet_stats:
                print(f"[{current_time}] No DDS packets detected")
                return
            
            print(f"\n[{current_time}] DDS Packet Statistics:")
            print("-" * 60)
            print(f"{'Source IP':<15} {'Packets':<10} {'Bytes':<15} {'Rate (pkt/s)':<12}")
            print("-" * 60)
            
            total_packets = sum(self.packet_stats.values())
            total_bytes = sum(self.byte_stats.values())
            
            # Sort by packet count (descending)
            sorted_ips = sorted(self.packet_stats.keys(), 
                              key=lambda x: self.packet_stats[x], reverse=True)
            
            for ip in sorted_ips:
                packets = self.packet_stats[ip]
                bytes_count = self.byte_stats[ip]
                rate = packets / self.report_interval
                
                print(f"{ip:<15} {packets:<10} {self.format_bytes(bytes_count):<15} {rate:<12.1f}")
            
            print("-" * 60)
            print(f"{'Total':<15} {total_packets:<10} {self.format_bytes(total_bytes):<15} {total_packets/self.report_interval:<12.1f}")
            print("-" * 60)
            
            # Reset statistics for next interval
            self.packet_stats.clear()
            self.byte_stats.clear()
    
    def stats_reporter(self):
        while self.running:
            time.sleep(self.report_interval)
            if self.running:
                self.print_stats()
    
    def packet_listener(self):
        while self.running:
            if not self.sockets:
                time.sleep(0.1)
                continue
            
            # Use select to wait for data on any socket
            ready_sockets, _, _ = select.select(self.sockets, [], [], 0.1)
            
            for sock in ready_sockets:
                try:
                    data, addr = sock.recvfrom(65536)
                    self.process_packet(data, addr)
                except socket.error:
                    # No data available or socket error
                    continue
    
    def cleanup_sockets(self):
        for sock in self.sockets:
            try:
                sock.close()
            except:
                pass
        self.sockets.clear()
    
    def start_monitoring(self):
        print(f"Starting DDS packet monitoring (report interval: {self.report_interval}s)")
        print("No root privileges required!")
        print("Press Ctrl+C to stop monitoring...")
        print("=" * 60)
        
        self.setup_sockets()
        
        if not self.sockets:
            print("Error: Could not set up any multicast listeners.")
            print("This might happen if:")
            print("1. No DDS nodes are currently running")
            print("2. Firewall is blocking multicast traffic")
            print("3. Network interface doesn't support multicast")
            return
        
        self.running = True
        
        # Start packet listening thread
        listener_thread = threading.Thread(target=self.packet_listener, daemon=True)
        listener_thread.start()
        
        # Start statistics reporting thread
        stats_thread = threading.Thread(target=self.stats_reporter, daemon=True)
        stats_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping DDS packet monitoring...")
        finally:
            self.running = False
            self.cleanup_sockets()
            # Print final statistics
            self.print_stats()


def monitor_dds_packets_no_sudo(report_interval: float = 5.0):
    monitor = DDSSocketMonitor(report_interval)
    monitor.start_monitoring()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor DDS packets without root privileges")
    parser.add_argument("-i", "--interval", type=float, default=5.0,
                        help="Report interval in seconds (default: 5.0)")
    
    args = parser.parse_args()
    
    monitor_dds_packets_no_sudo(args.interval)


if __name__ == "__main__":
    main()