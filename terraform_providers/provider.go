package main

import (
	"context"

	"github.com/Juniper/junos-terraform/terraform_providers/netconf"
	"github.com/hashicorp/terraform-plugin-framework/datasource"
	"github.com/hashicorp/terraform-plugin-framework/provider"
	"github.com/hashicorp/terraform-plugin-framework/provider/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/types"
)

var _ provider.Provider = new(Provider)

func newProvider() provider.Provider {
	return Provider{}
}

type Provider struct {
}

type providerModel struct {
	Dir types.String `tfsdk:"dir"`
}

// ProviderConfig is to hold client information
type ProviderConfig struct {
	netconf.Client
	Host string
}

// Configure implements provider.Provider.
func (p Provider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
	var config providerModel
	d := req.Config.Get(ctx, &config)
	resp.Diagnostics.Append(d...)
	if resp.Diagnostics.HasError() {
		return
	}
	resp.ResourceData = config.Dir.ValueString()
}

// DataSources implements provider.Provider.
func (p Provider) DataSources(_ context.Context) []func() datasource.DataSource {
	return nil
}

// Metadata implements provider.Provider.
func (p Provider) Metadata(_ context.Context, _ provider.MetadataRequest, resp *provider.MetadataResponse) {
	resp.TypeName = "toy"
}

// Resources implements provider.Provider.
func (p Provider) Resources(_ context.Context) []func() resource.Resource {
	return []func() resource.Resource{
		func() resource.Resource {
			return new(resourceInterfacesInterfaceUnitFamilyInetAddressName)
		},
	}
}

// Schema implements provider.Provider.
func (p Provider) Schema(_ context.Context, _ provider.SchemaRequest, resp *provider.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"dir": schema.StringAttribute{
				Required: true,
			},
		},
	}
}
