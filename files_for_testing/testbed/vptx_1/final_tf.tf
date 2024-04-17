terraform {
	required_providers {
		jtaf = {
			source = "juniper/providers/jtaf"
			version = "23.11.101"
		}
	}
}

resource "jtaf_InterfacesInterfaceUnitFamilyInetAddressName" "foo" {
	resource_name = "foo"
	name = "et-0/0/0"
	name__1 = "0"
	name__2 = "10.0.0.1/30"
}

