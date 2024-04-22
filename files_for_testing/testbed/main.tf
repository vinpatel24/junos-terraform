# replace {text} with your own test setup

terraform {
	required_providers {
		jtaf= {
			source = "juniper/providers/jtaf"
			version = "23.11.101"
		}
	}
}

provider "jtaf" {
	host = "66.129.234.208"
	port = 48012
	username = "jcluser"
	password = "Juniper!1"
	sshkey = ""
}

module "vptx_1" {
	source = "./vptx_1"

	providers = {jtaf= jtaf}

	depends_on = [jtaf_destroycommit.commit-main]
}


resource "jtaf_JunosDeviceCommit" "commit-main" {
	resource_name = "commit"
	depends_on = [module.vptx]
}

resource "jtaf_JunosDestroyCommit" "commit-main" {
	resource_name = "destroycommit"
}
	