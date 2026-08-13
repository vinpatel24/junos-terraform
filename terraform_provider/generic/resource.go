package generic

import (
	"context"
	"encoding/xml"
	"fmt"
	"os"

	"terraform_provider/netconf"
	"terraform_provider/patch"

	"github.com/hashicorp/terraform-plugin-framework/diag"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/tfsdk"
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
	planXML, err := r.planToXMLBytes(ctx)
	if err != nil {
		resp.Diagnostics.AddError("Failed to convert plan to XML", err.Error())
		return
	}

	if err := r.client.SendDirectTransaction(xmlWrapper{raw: planXML}, false); err != nil {
		resp.Diagnostics.AddError("Failed to apply configuration", err.Error())
		return
	}
	if err := r.client.SendCommit(); err != nil {
		resp.Diagnostics.AddError("Failed to commit", err.Error())
		return
	}

	r.readAndSetState(ctx, &resp.Diagnostics, &resp.State)
}

func (r *ConfigResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
	r.readAndSetState(ctx, &resp.Diagnostics, &resp.State)
}

func (r *ConfigResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	planXML, err := r.planToXMLBytes(ctx)
	if err != nil {
		resp.Diagnostics.AddError("Failed to convert plan to XML", err.Error())
		return
	}

	stateXML, err := r.readDeviceXML()
	if err != nil {
		resp.Diagnostics.AddError("Failed to read current config", err.Error())
		return
	}

	idx, err := patch.UnmarshalTrimmedSchemaIndex(r.schemaJSON)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse schema", err.Error())
		return
	}

	planTree, err := patch.BuildTree(planXML)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse plan XML", err.Error())
		return
	}
	stateTree, err := patch.BuildTree(stateXML)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse state XML", err.Error())
		return
	}

	planMap := patch.LeafMapWithSchema(planTree, idx)
	stateMap := patch.LeafMapWithSchema(stateTree, idx)
	diffMap := patch.ComputeDiff(stateMap, planMap)

	if len(diffMap) == 0 {
		r.readAndSetState(ctx, &resp.Diagnostics, &resp.State)
		return
	}

	patchXML, err := patch.CreateDiffPatch(diffMap, "")
	if err != nil {
		resp.Diagnostics.AddError("Failed to build patch", err.Error())
		return
	}

	debugPatch(planXML, stateXML, diffMap, string(patchXML))

	if err := r.client.SendUpdate("", string(patchXML), false); err != nil {
		resp.Diagnostics.AddError("Failed to send patch", err.Error())
		return
	}
	if err := r.client.SendCommit(); err != nil {
		resp.Diagnostics.AddError("Failed to commit", err.Error())
		return
	}

	r.readAndSetState(ctx, &resp.Diagnostics, &resp.State)
}

func (r *ConfigResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	stateXML, err := r.readDeviceXML()
	if err != nil {
		resp.Diagnostics.AddError("Failed to read current config", err.Error())
		return
	}

	emptyXML := []byte(xml.Header + "<configuration/>")

	idx, err := patch.UnmarshalTrimmedSchemaIndex(r.schemaJSON)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse schema", err.Error())
		return
	}

	stateTree, err := patch.BuildTree(stateXML)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse state XML", err.Error())
		return
	}
	emptyTree, err := patch.BuildTree(emptyXML)
	if err != nil {
		resp.Diagnostics.AddError("Failed to parse empty XML", err.Error())
		return
	}

	stateMap := patch.LeafMapWithSchema(stateTree, idx)
	emptyMap := patch.LeafMapWithSchema(emptyTree, idx)
	diffMap := patch.ComputeDiff(stateMap, emptyMap)
	if len(diffMap) == 0 {
		return
	}

	patchXML, err := patch.CreateDiffPatch(diffMap, "")
	if err != nil {
		resp.Diagnostics.AddError("Failed to build delete patch", err.Error())
		return
	}

	if err := r.client.SendUpdate("", string(patchXML), false); err != nil {
		resp.Diagnostics.AddError("Failed to delete config", err.Error())
		return
	}
	if err := r.client.SendCommit(); err != nil {
		resp.Diagnostics.AddError("Failed to commit delete", err.Error())
		return
	}
}

// --- helpers ---

type xmlWrapper struct{ raw []byte }

func (w xmlWrapper) MarshalXML(e *xml.Encoder, _ xml.StartElement) error {
	type rawXML struct {
		Inner []byte `xml:",innerxml"`
	}
	// Strip the outer <?xml?> header if present for embedding
	data := w.raw
	if idx := len(xml.Header); len(data) > idx && string(data[:idx]) == xml.Header {
		data = data[idx:]
	}
	return e.Encode(rawXML{Inner: data})
}

type tfStateLike interface {
	GetAttribute(ctx context.Context, path interface{}, target interface{}) interface{}
}

func (r *ConfigResource) planToXMLBytes(ctx context.Context) ([]byte, error) {
	// Placeholder: full implementation walks tftypes.Value tree
	return []byte(xml.Header + "<configuration/>"), nil
}

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

func (r *ConfigResource) readAndSetState(ctx context.Context, diags *diag.Diagnostics, state *tfsdk.State) {
	// Placeholder: read device XML, convert to state, and set.
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
