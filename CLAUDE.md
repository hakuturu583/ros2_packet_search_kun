# ROS2 Packet Search Kun

## Project Overview
A Python package for ROS2 packet searching functionality.

## Project Structure
```
├── src/
│   └── ros2_packet_search_kun/
│       ├── __init__.py
│       └── py.typed
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

## Development Information
- **Language**: Python (>=3.10)
- **Build System**: Hatchling
- **Package Name**: ros2-packet-search-kun
- **Version**: 0.1.0
- **Author**: Masaya Kataoka (ms.kataoka@gmail.com)

## Build Commands
- Build: `python -m build`
- Install: `pip install -e .`
- Run: `dds-monitor`

## Features
- Socket-based DDS packet monitoring (no sudo required)
- Real-time packet statistics by source IP
- Configurable reporting intervals
- RTPS header detection

## Usage
```bash
# Install and run
pip install -e .
dds-monitor --interval 5.0
```

## Implementation
- `dds_socket_monitor.py`: Main monitoring functionality using multicast sockets
- No external dependencies required
- Works with any ROS2 installation