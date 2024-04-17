# replace {text} with your own test setup

terraform {
	required_providers {
		junos-vptx = {
			source = "juniper/providers/junos-vptx"
			version = "23.11.101"
		}
	}
}

provider "junos-vptx" {
	host = "66.129.234.208"
	port = 33012
	username = "jcluser"
	password = "Juniper!1"
	sshkey = ""
}

module "vptx_1" {
	source = "./vptx_1"

	providers = {junos-vptx = junos-vptx}

	depends_on = [junos-vptx_destroycommit.commit-main]
}


resource "junos-vptx_commit" "commit-main" {
	resource_name = "commit"
	depends_on = [module.vptx]
}

resource "junos-vptx_destroycommit" "commit-main" {
	resource_name = "destroycommit"
}
	