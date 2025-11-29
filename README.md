# LANdToss

Allows devices connected to the same network to swiftly transfer files.

## Quick Start

Navigate to your folder and clone repo:
```bash
git clone https://github.com/oh-nought/LANdToss
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create an `.env` file and paste the following into it:
```
HOST=0.0.0.0
PORT=8000
```

Run the program:
```bash
python server.py
```

## How to use LANdToss
After running the program, you will be prompted with something like this:

```bash
LANdToss Server


    Visit: http://[your host]:[your port] to connect
          
        
INFO:     Started server process [94048]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
...
```

Upon connecting to the page, users will be given a unique name and id. Take note of your name as well as the name of the device you want to send to and after uploading your files, select their names and toss!