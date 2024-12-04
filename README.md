# Multi-Antivirus File Scanning System

[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/NNNN/badge)](https://bestpractices.coreinfrastructure.org/projects/NNNN)

_Note: Replace NNNN with your actual project ID after registering with CII Best Practices_

## Overview

This project provides a robust, multi-layered file scanning system using multiple antivirus engines in a containerized environment. The system monitors a target folder, moves files to storage, and scans them using ClamAV, eScan, McAfee, and Comodo antivirus solutions.

## Prerequisites

- Docker
- Docker Compose
- Git

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-antivirus-scanner.git
cd multi-antivirus-scanner
```

### 2. Update Antivirus Containers (Optional)

Run the development script to update antivirus containers:

```bash
chmod +x dev-script.sh
./dev-script.sh
```

### 3. Build and Run

```bash
docker-compose up --build
```

## Project Structure

```
.
├── dev-script.sh              # Script to update antivirus containers
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image build instructions
├── monitor.py                 # Main monitoring and scanning script
├── requirements.txt           # Python dependencies
├── storage/                   # Directory for scanned files
└── target-folder/             # Directory for files to be scanned
```

## How It Works

1. Place files in the `target-folder/` directory
2. The system automatically:
   - Moves files to the `storage/` directory
   - Scans files using multiple antivirus engines
   - Generates metadata with scan results
3. Scan results are stored as JSON metadata files alongside the scanned files

## Configuration

### Antivirus Services

The system currently supports:

- ClamAV
- eScan
- McAfee
- Comodo

Each service is run in a separate Docker container and communicates via a bridge network.

### Customization

Modify `monitor.py` to:

- Change watched directory
- Add or remove antivirus engines
- Adjust scanning logic

## Requirements

Python dependencies are managed in `requirements.txt`:

- watchdog
- requests
- flask
- pyclamd

## Scan Results

For each file, a `.metadata.json` file is created with:

- Unique ID
- Timestamp
- File type
- Host path
- Antivirus scan results

## Security Considerations

- Files are moved to a separate storage directory before scanning
- Multiple antivirus engines provide comprehensive protection
- Metadata tracks file origins and scan results

## Troubleshooting

- Ensure Docker and Docker Compose are properly installed
- Check Docker logs for detailed error messages
- Verify network connectivity between containers

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the [Your License]. See `LICENSE` for more information.

## Contact

[Your Name] - [your.email@example.com]

Project Link: [https://github.com/yourusername/multi-antivirus-scanner](https://github.com/yourusername/multi-antivirus-scanner)
