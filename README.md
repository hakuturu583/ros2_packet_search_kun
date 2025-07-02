# ROS2 Packet Search Kun

A Python package for monitoring and analyzing DDS (Data Distribution Service) packets used by ROS2.

## Features

- Monitor DDS broadcast packets in real-time
- Track packet statistics by source IP address
- Display periodic reports with packet counts and data volumes
- Support for filtering by network interface
- Configurable reporting intervals

## Installation

```bash
pip install -e .
```

## Usage

### Command Line Interface

Monitor DDS packets with default settings (5-second intervals):
```bash
dds-monitor
```

Monitor with custom interval:
```bash
dds-monitor --interval 10.0
```

### Python API

```python
from ros2_packet_search_kun import monitor_dds_packets_no_sudo, DDSSocketMonitor

# Monitor with default settings
monitor_dds_packets_no_sudo()

# Monitor with custom settings
monitor_dds_packets_no_sudo(report_interval=10.0)

# Use the class directly for more control
monitor = DDSSocketMonitor(report_interval=5.0)
monitor.start_monitoring()
```

## Requirements

- Python 3.10+
- No root privileges required!

## How It Works

The tool uses socket-based multicast listening to capture DDS traffic:

1. **Multicast Sockets**: Creates UDP sockets that join DDS multicast groups (239.255.0.x range)
2. **Port Monitoring**: Listens on common DDS discovery ports (7400-7411)
3. **RTPS Detection**: Identifies packets with RTPS (Real-Time Publish-Subscribe) headers
4. **No Privileges**: Uses standard Python sockets - no root access required!

## Output Format

```
[2024-01-01 12:00:00] DDS Packet Statistics:
------------------------------------------------------------
Source IP       Packets    Bytes           Rate (pkt/s)
------------------------------------------------------------
192.168.1.100   45         12.3 KB         9.0
192.168.1.101   23         6.7 KB          4.6
------------------------------------------------------------
Total           68         19.0 KB         13.6
------------------------------------------------------------
```

[ros2_packet_search_kun.webm](https://github.com/user-attachments/assets/bd55c93e-3cb6-4de9-a045-9db5edcb1a01)

## License

MIT License
