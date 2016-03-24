Vagrant.configure(2) do |config|

  config.vm.provider :libvirt do |libvirt|
    # FIXES: https://github.com/mitchellh/vagrant/issues/1673
    config.ssh.shell = "bash -c 'BASH_ENV=/etc/profile exec bash'"

    libvirt.connect_via_ssh = true
    libvirt.host = "host.acionconsultancy.int"
    libvirt.username = "root"

    libvirt.storage_pool_name = "default"

    config.vm.network :private_network,
    	:ip => "169.254.254.13",
    	:libvirt__netmask => "255.255.255.0",
    	:libvirt__host_ip => "169.254.254.1",
    	:libvirt__network_name => "default",
    	:libvirt__forward_mode => "none"

    libvirt.cpus = 1
    libvirt.memory = 2560
    libvirt.random_hostname = true
    libvirt.volume_cache = "unsafe"

    config.vm.box = "ubuntu-1504-server"
  end

  config.vm.synced_folder ".", "/vagrant/"

  config.vm.provision "shell", inline: <<-SHELL

sudo ifdown eth{2,3} # vagrant-libvirt madness :(

bash /vagrant/files/provision.sh

  SHELL

end
