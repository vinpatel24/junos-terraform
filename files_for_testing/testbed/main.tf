# replace {text} with your own test setup

terraform {
	required_providers {
		junos-vqfx = {
			source = "juniper/providers/junos-vqfx"
			version = "23.11.101"
		}
	}
}

provider "junos-vqfx" {
	host = "localhost"
	port = 8300
	username = "root"
	password = "juniper123"
	sshkey = ""
}

module "vqfx_1" {
	source = "./vqfx_1"

	providers = {junos-vqfx = junos-vqfx}

	depends_on = [junos-vqfx_destroycommit.commit-main]
}


resource "junos-vqfx_commit" "commit-main" {
	resource_name = "commit"
	depends_on = [module.vqfx]
}

resource "junos-vqfx_destroycommit" "commit-main" {
	resource_name = "destroycommit"
}
	