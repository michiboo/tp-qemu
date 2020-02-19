import logging
from virttest import error_context
import os 
from qemu.tests.virtio_serial_file_transfer import transfer_data
from avocado.utils import process

@error_context.context_aware
def run(test, params, env):
    """
    Induce throttling by opening chardev but not reading data from it:
    1) Start guest with virtio-serial with unix option
    2) On the host, open the chardev but don't read from it
    3) In the guest, write to the virtio-serial port.
    4) repeat step 1 to 3 with tcp option.
    :param test: QEMU test object
    :param params: Dictionary with the test parameters
    :param env: Dictionary with test environment.
    """

    vm = env.get_vm(params["main_vm"])
    vm.verify_alive()
    session = vm.wait_for_login()
    cmd = "path='/tmp/port0';import socket; sock = socket.socket(socket.AF_UNIX);sock.connect(path);"
    process.run('touch /tmp/port0')
    os.system('python3 -c \"{}\"&'.format(cmd).strip())
    a = session.cmd_output('dd if=/dev/zero of=/dev/vport0p2')
    transfer_data(params, vm, sender='host')
    os.system('python3 -c \"{}\"&'.format(cmd).strip())
    a = session.cmd_output('dd if=/dev/zero of=/dev/vport0p2')

    vm.destroy()
    params['chardev_backend_vs1'] = 'tcp_socket'
    vm.create(params=params)
    vm.verify_alive()
    session = vm.wait_for_login()
    cmd = "import socket;sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);sock.connect(('10.66.82.249', 5555))"
    os.system('python3 -c \"{}\"&'.format(cmd).strip())
    a = session.cmd_output('dd if=/dev/zero of=/dev/vport0p2')
    transfer_data(params, vm, sender='host')
    os.system('python3 -c \"{}\"&'.format(cmd).strip())
    a = session.cmd_output('dd if=/dev/zero of=/dev/vport0p2')
    os.system("kill $(ps -elf | grep 'python3 -c' | awk '{print $4}')")