import sys
import binascii
from can2RNET.RnetDissector.RnetDissector import printFrame

if __name__ == "__main__":
    if len(sys.argv) == 2:
        with open(sys.argv[1], "r") as f:
            for l in f.readlines():
                w = l.split(":")
                h = w[2].split("'")[1]
                print(printFrame(binascii.unhexlify(h)))
    else:
        print("Usage: %s log_file" % sys.argv[0])
