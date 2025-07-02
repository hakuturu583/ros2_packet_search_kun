import time
import threading
from datetime import datetime
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from .dds_socket_monitor import DDSSocketMonitor


class PrometheusExporter:
    def __init__(self, port: int = 8000, monitor_interval: float = 5.0):
        self.port = port
        self.monitor_interval = monitor_interval
        
        # Prometheus metrics
        self.packet_counter = Counter(
            'dds_packets_total',
            'Total number of DDS packets received',
            ['source_ip']
        )
        
        self.byte_counter = Counter(
            'dds_bytes_total',
            'Total bytes of DDS packets received',
            ['source_ip']
        )
        
        self.packet_rate = Gauge(
            'dds_packet_rate',
            'DDS packet rate per second',
            ['source_ip']
        )
        
        self.active_sources = Gauge(
            'dds_active_sources',
            'Number of active DDS sources'
        )
        
        self.packet_size_histogram = Histogram(
            'dds_packet_size_bytes',
            'Distribution of DDS packet sizes',
            ['source_ip']
        )
        
        # Custom DDS monitor
        self.monitor = DDSSocketMonitor(monitor_interval)
        
        # Override the print_stats method to export to Prometheus
        self.monitor.print_stats = self.export_metrics
    
    def export_metrics(self):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self.monitor.stats_lock:
            if not self.monitor.packet_stats:
                print(f"[{current_time}] No DDS packets detected")
                self.active_sources.set(0)
                return
            
            print(f"[{current_time}] Exporting DDS metrics to Prometheus...")
            
            # Update Prometheus metrics
            total_packets = 0
            total_bytes = 0
            
            for ip, packet_count in self.monitor.packet_stats.items():
                byte_count = self.monitor.byte_stats[ip]
                rate = packet_count / self.monitor_interval
                avg_size = byte_count / packet_count if packet_count > 0 else 0
                
                # Update counters
                self.packet_counter.labels(source_ip=ip).inc(packet_count)
                self.byte_counter.labels(source_ip=ip).inc(byte_count)
                
                # Update gauges
                self.packet_rate.labels(source_ip=ip).set(rate)
                
                # Update histogram
                for _ in range(packet_count):
                    self.packet_size_histogram.labels(source_ip=ip).observe(avg_size)
                
                total_packets += packet_count
                total_bytes += byte_count
                
                print(f"  {ip}: {packet_count} packets, {self.format_bytes(byte_count)}, {rate:.1f} pkt/s")
            
            # Update active sources count
            self.active_sources.set(len(self.monitor.packet_stats))
            
            print(f"  Total: {total_packets} packets, {self.format_bytes(total_bytes)}")
            print(f"  Active sources: {len(self.monitor.packet_stats)}")
            print(f"  Metrics available at: http://localhost:{self.port}/metrics")
            print("-" * 60)
            
            # Reset statistics for next interval
            self.monitor.packet_stats.clear()
            self.monitor.byte_stats.clear()
    
    def format_bytes(self, bytes_count: int) -> str:
        if bytes_count < 1024:
            return f"{bytes_count} B"
        elif bytes_count < 1024 * 1024:
            return f"{bytes_count / 1024:.1f} KB"
        elif bytes_count < 1024 * 1024 * 1024:
            return f"{bytes_count / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_count / (1024 * 1024 * 1024):.1f} GB"
    
    def start(self):
        print(f"Starting Prometheus exporter on port {self.port}")
        print(f"DDS monitoring interval: {self.monitor_interval}s")
        print(f"Metrics endpoint: http://localhost:{self.port}/metrics")
        print("=" * 60)
        
        # Start Prometheus HTTP server
        start_http_server(self.port)
        
        # Start DDS monitoring
        self.monitor.start_monitoring()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Export DDS packet metrics to Prometheus")
    parser.add_argument("-p", "--port", type=int, default=8000,
                        help="Prometheus metrics port (default: 8000)")
    parser.add_argument("-i", "--interval", type=float, default=5.0,
                        help="DDS monitoring interval in seconds (default: 5.0)")
    
    args = parser.parse_args()
    
    exporter = PrometheusExporter(port=args.port, monitor_interval=args.interval)
    exporter.start()


if __name__ == "__main__":
    main()