import sys
import binascii
from can2RNET.RnetDissector.RnetDissector import printFrame

count = 0

if __name__ == "__main__":
    if len(sys.argv) == 3:
        with open(sys.argv[2], 'w') as out:
            with open(sys.argv[1], "r") as f:
                for l in f.readlines():
                    w = l.split(":")
                    h = w[2].split("'")[1]
                    out.write("%d %s : %s\n" %(count, w[1], printFrame(binascii.unhexlify(h))))
                    count += 1
    else:
        print("Usage: %s log_file" % sys.argv[0])
