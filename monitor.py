import subprocess
from time import sleep


class sensors:
    def __init__(self, sensor_output):
        self.temp = 0
        self.fans = list()
        self.fan_speed = dict()
        self.cpu_temp = dict()
        self.cores = dict()

        lines = iter(sensor_output.splitlines())
        for line in lines:
            if line.startswith(b'fan'):
                fan = line[0:line.find(b':')]
                speed = line[line.find(b':'):line.find(b'RPM')].strip()
                self.fans.append(fan)
                self.fan_speed[fan] = speed
            elif line.startswith(b'temp'):
                self.temp = float(line[line.find(b':') + 1:line.find(b'\xc2\xb0C')])
            elif line.startswith(b'coretemp'):
                _ = next(lines)
                line = next(lines)
                cpu = line[0:line.find(b':')]
                cpu = cpu[cpu.rfind(b' ') + 1:]
                temp = line[line.find(b':'):line.find(b'\xc2\xb0C')].strip()
                cpu_index = int(cpu)
                self.cpu_temp[cpu_index] = temp

            elif line.startswith(b'Core'):
                core = line[0:line.find(b':')]
                core = core[core.find(b' ') + 1:].strip()
                temp = line[line.find(b':') + 1:line.find(b'\xc2\xb0C')].strip()
                if not self.cores.get(cpu_index):
                    self.cores[cpu_index] = {}
                self.cores[cpu_index][int(core)] = float(temp)

    def core_temp(self, core, temp):
        self.cpu_temp[core] = temp

    def cpu_core_temp(self, cpu, core, temp):
        self.cpu[cpu][core] = temp

    def fan_speed(self, fan, speed):
        self.fan_speed[fan] = speed

    def set_temp(self, temp):
        self.temp = temp

    def read_sensor_output(self, sensor_output):
        lines = iter(sensor_output.splitlines())
        for line in lines:
            if line.startswith(b'fan'):
                fan = line[0:line.find(b':')]
                speed = line[line.find(b':'):line.find(b'RPM')].strip()
                self.fan_speed[fan] = speed
            elif line.startswith(b'temp'):
                self.temp = float(line[line.find(b':') + 1:line.find(b'\xc2\xb0C')])
            elif line.startswith(b'coretemp'):
                _ = next(lines)
                line = next(lines)
                cpu = line[0:line.find(b':')]
                cpu = cpu[cpu.rfind(b' ') + 1:]
                temp = line[line.find(b':'):line.find(b'\xc2\xb0C')].strip()
                cpu_index = int(cpu)
                self.cpu_temp[cpu_index] = temp

            elif line.startswith(b'Core'):
                core = line[0:line.find(b':')]
                core = core[core.find(b' ') + 1:].strip()
                temp = line[line.find(b':') + 1:line.find(b'\xc2\xb0C')].strip()
                self.cores[cpu_index][int(core)] = float(temp)

    def get_core_temperatures(self):
        temperatures = [0] * sum(len(v) for v in self.cores.values())
        core_index = 0
        for cpu in self.cores:
            for core in self.cores[cpu]:
                temperatures[core_index] = self.cores[cpu][core]
                core_index += 1

        print(core_index)
        return (temperatures)


sensor = sensors(subprocess.check_output('sensors'))

while True:
    sensor.read_sensor_output(subprocess.check_output('sensors'))
    print(sensor.get_core_temperatures())
    sleep(1)




