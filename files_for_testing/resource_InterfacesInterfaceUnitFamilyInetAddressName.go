package main

import (
	"context"
	"encoding/xml"
	"strings"

	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/planmodifier"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/stringplanmodifier"
	"github.com/hashicorp/terraform-plugin-framework/types"
)

// v_ is appended before every variable so it doesn't give any conflict
// with any keyword in golang. ex - interface is keyword in golang
type xmlInterfacesInterfaceUnitFamilyInetAddressName struct {
	XMLName xml.Name `xml:"configuration"`
	Groups  struct {
		XMLName     xml.Name `xml:"groups"`
		Name        string   `xml:"name"`
		V_interface struct {
			XMLName xml.Name `xml:"interface"`
			V_name  *string  `xml:"name,omitempty"`
			V_unit  struct {
				XMLName   xml.Name `xml:"unit"`
				V_name__1 *string  `xml:"name,omitempty"`
				V_address struct {
					XMLName   xml.Name `xml:"address"`
					V_name__2 *string  `xml:"name,omitempty"`
				} `xml:"family>inet>address"`
			} `xml:"unit"`
		} `xml:"interfaces>interface"`
	} `xml:"groups"`
}

// Collects the objects from the .tf file
type interfacesInterfaceUnitFamilyInetAddressNameModel struct {
	ResourceName types.String `tfsdk:"resource_name"`
	Name         types.String `tfsdk:"name"`
	Name1        types.String `tfsdk:"name__1"`
	Name2        types.String `tfsdk:"name__2"`
}

// Collects the data for the crud work
type resourceInterfacesInterfaceUnitFamilyInetAddressName struct {
	client ProviderConfig
}

func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Configure(_ context.Context, req resource.ConfigureRequest, _ *resource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}
	r.client = req.ProviderData.(ProviderConfig)
}

// Metadata implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_InterfacesInterfaceUnitFamilyInetAddressName"
}

// Schema implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Schema(_ context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"resource_name": schema.StringAttribute{
				Required:      true,
				PlanModifiers: []planmodifier.String{stringplanmodifier.RequiresReplace()},
			},
			"name": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "xpath is: `config.Groups.V_interface`",
			},
			"name__1": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "xpath is: `config.Groups.V_interface.V_unit`",
			},
			"name__2": schema.StringAttribute{
				Required:            true,
				MarkdownDescription: "xpath is: `config.Groups.V_interface.V_unit.V_address`. Interface address/destination prefix",
			},
		},
	}
}

// Create implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {

	// Get the data and set
	var plan interfacesInterfaceUnitFamilyInetAddressNameModel
	resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
	if resp.Diagnostics.HasError() {
		return
	}

	var config xmlInterfacesInterfaceUnitFamilyInetAddressName
	config.Groups.Name = plan.ResourceName.ValueString()
	config.Groups.V_interface.V_name = plan.Name.ValueStringPointer()
	config.Groups.V_interface.V_unit.V_name__1 = plan.Name1.ValueStringPointer()
	config.Groups.V_interface.V_unit.V_address.V_name__2 = plan.Name2.ValueStringPointer()

	err := r.client.SendTransaction("", config, false)
	if err != nil {
		resp.Diagnostics.AddError("Failed while Sending", err.Error())
		return
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &plan)...)
}

// Read implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {

	// Get the data and set
	var state interfacesInterfaceUnitFamilyInetAddressNameModel
	resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
	if resp.Diagnostics.HasError() {
		return
	}

	// Marshall group and check
	var config xmlInterfacesInterfaceUnitFamilyInetAddressName
	err := r.client.MarshalGroup(state.Name.ValueString(), &config)
	if err != nil {
		if strings.Contains(err.Error(), "ound") {
			resp.State.RemoveResource(ctx)
			return
		}
		resp.Diagnostics.AddError("Failed while Reading", err.Error())
		return
	}

	state.Name = types.StringPointerValue(config.Groups.V_interface.V_name)
	state.Name1 = types.StringPointerValue(config.Groups.V_interface.V_unit.V_name__1)
	state.Name2 = types.StringPointerValue(config.Groups.V_interface.V_unit.V_address.V_name__2)

	resp.Diagnostics.Append(resp.State.Set(ctx, &state)...)
}

// Update implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	// Get the data and set
	var plan interfacesInterfaceUnitFamilyInetAddressNameModel

	resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
	if resp.Diagnostics.HasError() {
		return
	}

	var config xmlInterfacesInterfaceUnitFamilyInetAddressName
	config.Groups.Name = plan.ResourceName.ValueString()
	config.Groups.V_interface.V_name = plan.Name.ValueStringPointer()
	config.Groups.V_interface.V_unit.V_name__1 = plan.Name1.ValueStringPointer()
	config.Groups.V_interface.V_unit.V_address.V_name__2 = plan.Name2.ValueStringPointer()

	err := r.client.SendTransaction("", config, false)
	if err != nil {
		resp.Diagnostics.AddError("Failed while Sending", err.Error())
		return
	}

	resp.Diagnostics.Append(resp.State.Set(ctx, &plan)...)
}

// Delete implements resource.Resource.
func (r *resourceInterfacesInterfaceUnitFamilyInetAddressName) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var state interfacesInterfaceUnitFamilyInetAddressNameModel
	resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
	if resp.Diagnostics.HasError() {
		return
	}

	_, err := r.client.DeleteConfig(state.ResourceName.ValueString(), false)
	if err != nil {
		if strings.Contains(err.Error(), "ound") {
			return
		}
		resp.Diagnostics.AddError("Failed while deleting", err.Error())
		return
	}
}