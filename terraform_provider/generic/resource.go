package generic

import (
	"context"
	"encoding/xml"
	"fmt"
	"os"

	"terraform_provider/netconf"
	"terraform_provider/patch"

	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
)

// ConfigResource is the generic schema-driven resource.
type ConfigResource struct {
	client     netconf.Client
	host       string
	idx        map[string]*patch.NodeInfo
	nodes      []patch.SchemaNode
	tfSchema   schema.Schema
	schemaJSON string
}

// NewConfigResource creates a ConfigResource from pre-loaded schema data.
func NewConfigResource(idx map[string]*patch.NodeInfo, nodes []patch.SchemaNode, schemaJSON string) *ConfigResource {
	return &ConfigResource{
		idx:        idx,
		nodes:      nodes,
		tfSchema:   BuildSchema(nodes),
		schemaJSON: schemaJSON,
	}
}

// ProviderData is the interface the generic resource expects from provider configuration.
type ProviderData interface {
	GetClient() netconf.Client
	GetHost() string
}

func (r *ConfigResource) Configure(_ context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}
	pd, ok := req.ProviderData.(ProviderData)
	if !ok {
		resp.Diagnostics.AddError("Unexpected provider data type",
			fmt.Sprintf("Expected generic.ProviderData, got %T", req.ProviderData))
		return
	}
	r.client = pd.GetClient()
	r.host = pd.GetHost()
}

func (r *ConfigResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = "terraform-provider-" + req.ProviderTypeName
}

func (r *ConfigResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = r.tfSchema
}

func (r *ConfigResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	resp.State.Raw = req.Plan.Raw
}

func (r *ConfigResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	// Preserve existing state — read-back from device not yet wired.
}

func (r *ConfigResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	resp.State.Raw = req.Plan.Raw
}

func (r *ConfigResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
}

// --- helpers kept for future NETCONF wiring ---

func (r *ConfigResource) readDeviceXML() ([]byte, error) {
	type configuration struct {
		XMLName xml.Name `xml:"configuration"`
		Inner   []byte   `xml:",innerxml"`
	}
	var cfg configuration
	if err := r.client.MarshalConfig(&cfg); err != nil {
		return nil, err
	}
	return xml.Marshal(cfg)
}

func debugPatch(planXML, stateXML []byte, diffMap map[string]patch.Change, patchPayload string) {
	if os.Getenv("JUNOS_TF_DEBUG_PATCH") == "" {
		return
	}
	fmt.Printf("\n=== generic provider diff patch debug ===\n")
	fmt.Printf("--- state xml ---\n%s\n", string(stateXML))
	fmt.Printf("--- plan xml ---\n%s\n", string(planXML))
	fmt.Printf("--- diff map ---\n")
	for _, entry := range patch.DebugSortedChanges(diffMap) {
		fmt.Printf("%v | %s | old=%q | new=%q\n", entry.Op, entry.Path, entry.OldVal, entry.NewVal)
	}
	fmt.Printf("--- patch payload ---\n%s\n", patchPayload)
}
