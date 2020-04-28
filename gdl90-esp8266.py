import serial
import struct
import time
import threading

CRLF = '\r\n'.encode()


class Reader:
    def __init__(self, esp):
        self.serial = esp
        self.ready = True
        self.exit = False

    def __call__(self, *args, **kwargs):
        while not self.exit and threading.main_thread().is_alive() and self.serial.is_open:
            try:
                line_bytes = self.serial.read_until(CRLF)
            except TypeError:
                continue

            try:
                line = line_bytes.decode()
            except UnicodeDecodeError:
                line = str(line_bytes)

            print(line)
            if line.startswith("OK") or line.startswith("ERROR"):
                self.ready = True


def read_lines(esp, timeout=10):
    exit_time = time.time() + timeout
    while True:
        line = esp.read_until(CRLF).decode()
        yield line
        if line.startswith("OK") or line.startswith("ERROR"):
            break

        if time.time() > exit_time:
            break


def main():
    with serial.Serial('/dev/ttyUSB0', 115200, timeout=5) as esp:
        reader = Reader(esp)
        reader_thread = threading.Thread(target=reader)
        reader_thread.start()

        print("Reset")
        esp.write('AT+RST\r\n'.encode())

        print("Sleep")
        time.sleep(5)

        print("Test")
        reader.ready = False
        esp.write('AT\r\n'.encode())
        while not reader.ready:
            pass
        print("Done")

        reader.ready = False
        esp.write('AT+CIPSTATUS\r\n'.encode())
        while not reader.ready:
            pass

        print("Set station mode")
        reader.ready = False
        esp.write('AT+CWMODE_DEF=1\r\n'.encode())
        while not reader.ready:
            pass

        # print("Join access point")
        # reader.ready = False
        # esp.write('AT+CWJAP_DEF="stratux",""\r\n'.encode())
        # while not reader.ready:
        #     pass

        print("Listen UDP 4000")
        reader.ready = False
        esp.write('AT+CIPSTART="UDP","192.168.10.1",4000,4000\r\n'.encode())
        while not reader.ready:
            pass

        # print("Set receive mode")
        # reader.ready = False
        # esp.write('AT+CIPRECVMODE=0\r\n'.encode())
        # while not reader.ready:
        #     pass

        print("Stopping reader thread")
        reader.exit = True
        reader_thread.join()

        print("Watching output")
        try:
            udp_line_parser(esp)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(e)
            lines = 0
            while lines < 100:
                lines += 1
                line = esp.read_until(b'\r\n')
                print(line)


def udp_line_parser(esp):
    skipped = 0
    while True:
        try:
            start = esp.read(1)
            if start == b'+':
                # print(f"Got + after {skipped} skipped bytes")
                byte_count = 0
                header = b''

                length = 0
                while byte_count < 10:
                    byte_count += 1
                    next_byte = esp.read(1)
                    header += next_byte
                    if next_byte == b':':
                        if header.startswith(b'IPD,'):
                            len_bytes = header[4:].split(b':', maxsplit=1)[0]
                            length = int(len_bytes.decode())
                        break

                # print(f"Reading {length} bytes of GDL90 after {header}")

                gdl_message = esp.read(length)
                msg_id = gdl_message[1]
                if msg_id == 11:
                    alt = 5 * (gdl_message[2] * 256 + gdl_message[3])
                    print(f"GDL90 Altitude: {alt} ft")
                elif msg_id in [10, 11, 0]:
                    print(f"GDL90 ID#{msg_id}: {gdl_message}")
                skipped = 0
            else:
                skipped += 1
        except serial.serialutil.SerialException as err:
            print(err)


if __name__ == '__main__':
    main()
