from jinja2 import Template

def render_template(data):
    jinja_source = """
{############# COMMON VARIABLES # STARTS ################}
{%- set parent_list = data['root']['kids'][0]['kids']%}

{############### COMMON VARIABLES # ENDS ####################}

{############# COMMON MACROS #STARTS ################}
{%- macro get_full_parent_name(ele, sep, cap='False') %}
{%- set result_list = [] %}
{%- if ele['path'] is defined %}
{%- for item in ele['path'].split("/")%}
{%- if cap == 'True'%}
{{- result_list.append(item|capitalize|replace("-", "_")|replace(".", "_")|replace(".", "_")) or ""}}
{%- else %}
{{- result_list.append(item|replace("-", "_")|replace(".", "_")) or ""}}
{%- endif %}
{%- endfor %}
{%- endif %}
{{-result_list|join(sep)-}}
{%- endmacro %}

{%- macro get_parent_list_with_iterator(ele) -%}
{%- set result_list = [] %}
{%- set temp_list = []%}
{%- if ele['path'] is defined %}
{%- for item in ele['path'].split("/")%}
{{- temp_list.append(item|replace("-", "_")|replace(".", "_")) or ""}}
{%- set cap_item = item|capitalize|replace("-", "_")|replace(".", "_") %}
{{- result_list.append(cap_item+"[i_"+temp_list|join("_")+"]") or ""}}
{%- endfor %}
{%- endif %}
{{-result_list|join(".")-}}
{%- endmacro -%}

{%- macro string_macro(ele) -%}
		{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}         *string  `xml:"{{ele.name|replace("_","-")}},omitempty"`
{%- endmacro -%}

{%- macro bool_macro(ele) -%}
		{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}         *bool  `xml:"{{ele.name|replace("_","-")}},omitempty"`
{%- endmacro -%}

{%- macro int32_macro(ele) -%}
		{{ele.name|capitalize}}         *int32  `xml:"{{ele.name|replace("_","-")}},omitempty"`
{%- endmacro -%}

{%- macro list_macro(ele) -%}
		{%- if ele['path'] is defined %}
		{%- set parent_name = ele['path'].split("/")[-1] -%}
		{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}} []xml_{{get_full_parent_name(ele, "_", 'True')}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}} `xml:"{{ele.name}},omitempty"`	
		{%- endif %}
{%- endmacro -%}
{################ COMMON MACROS #ENDS ################}

{################ STATIC STATEMENTS #STARTS ###########}
package main

import (
	"context"
	"encoding/xml"
	"strings"
	"github.com/hashicorp/terraform-plugin-framework/attr"
	"github.com/hashicorp/terraform-plugin-framework/resource"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/planmodifier"
	"github.com/hashicorp/terraform-plugin-framework/resource/schema/stringplanmodifier"
	"github.com/hashicorp/terraform-plugin-framework/types"
)
{############### STATIC STATEMENTS #ENDS ###############}

{################ STRUCT FROM XML # STARTS #############}
{%- set ele_xml_struct = [] %}
{%- macro xml_struct_definition(parent, arg1) -%}
{%- if parent[0] is defined  %}
{%- set arg1 = []%}
{%- for ele in parent %}
type xml_{{get_full_parent_name(ele, "_", 'True')}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}} struct {
	XMLName xml.Name `xml:"{{ele.name}}"`
	{%- if ele.kids %}
	{%- for kid in ele['kids'] %}
	{%- if (kid['leaf-type'] == 'string') or (kid['base-type'] == 'string') or (kid['leaf-type']== 'empty') or (kid['leaf-type']== 'union') or (kid['type']== 'leaf-list') or (kid['leaf-type']== 'enumeration') or (kid['type']== 'empty')%}
	{{string_macro(kid)}}
	{%- endif %}
	{%- if (kid['type'] == 'container') or (kid['type'] == 'list') %}
	{{list_macro(kid)}}
	{%- if arg1.append(kid) %}{%- endif %}
	{%- endif %}
	{%- endfor %}
	{%- endif %}
}
{%- endfor %}
{%- if arg1|length > 0 %}
{{xml_struct_definition(arg1, arg0)}}
{%- endif %}
{%- endif %}
{%- endmacro -%}
// Junos XML Hierarchy

type xml_Configuration struct {
	XMLName xml.Name `xml:"configuration"`
	Groups struct {
		XMLName xml.Name `xml:"groups"`
		Name    *string   `xml:"name"`
		{%- for parent in parent_list %}
		{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} []xml_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} `xml:"{{parent.name}},omitempty"`
		{%- endfor %}
	}
}
{%- for parent in parent_list %}
type xml_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} struct {
	XMLName xml.Name `xml:"{{parent.name}}"`
	{%- for kid in parent['kids'] %}
	{%- if (kid['leaf-type'] == 'string') or (kid['base-type'] == 'string') or (kid['leaf-type']== 'empty') or (kid['leaf-type']== 'union') or (kid['type']== 'leaf-list') or (kid['leaf-type']== 'enumeration')%}
	{{string_macro(kid)}}
	{%- endif %}
	{%- if kid['type'] == 'list' or kid['type'] == 'container'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} []xml_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} `xml:"{{kid.name}},omitempty"`
    {%- if ele_xml_struct.append(kid) %}{%- endif %}
	{%- endif %}
	{%- endfor %}
}
{% endfor %}
{% if ele_xml_struct|length > 0%}
{{- xml_struct_definition(ele_xml_struct, arg1)}}
{%- endif %}
{##################### STRUCT FROM XML #ENDS ###################}

{########################## STRUCT FROM TF # STARTS ############}

{%- set ele_for_struct = [] %}

{%- macro create_struct(ele, arg2) %}
{%- if ele[0] is defined  %}
{%- set arg2 = []%}
{%- for parent in ele %}
type {{get_full_parent_name(parent, "_", 'True')}}_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model struct {
	{%- for kid in parent['kids'] %}
	{%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}	types.String `tfsdk:"{{kid.name|replace("-", "_")|replace(".", "_")}}"`
	{%- endif %}
	{# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} types.Bool `tfsdk:"{{kid.name|replace("-", "_")|replace(".", "_")}}"`
	{%- endif %} #}
	{%- if kid['type'] == 'container' or kid['type'] == 'list'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}	types.List `tfsdk:"{{kid.name|replace("-", "_")|replace(".", "_")}}"`
	{%- if arg2.append(kid) %} {% endif %}
	{%- endif %}
	{%- endfor %}
}
func (o {{get_full_parent_name(parent, "_", 'True')}}_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model) AttrTypes() map[string]attr.Type {
	return map[string]attr.Type{
	    {%- for kid in parent['kids'] %}
	    {%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": 	types.StringType,
	    {%- endif %}
	    {# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty' %}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": 	types.BoolType,
	    {%- endif %} #}
	    {%- if kid['type'] == 'list' or kid['type'] == 'container'%}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": 	types.ListType{ElemType: types.ObjectType{AttrTypes: {{get_full_parent_name(kid, "_", 'True')}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.AttrTypes()}},
	    {%- endif %}
	    {%- endfor %}
	}
}
func (o {{get_full_parent_name(parent, "_", 'True')}}_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model) Attributes() map[string]schema.Attribute {
	return map[string]schema.Attribute{
	    {%- for kid in parent['kids'] %}
	    {%- if kid['leaf-type'] == 'string'or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": schema.StringAttribute{
		    Optional: true,
		    MarkdownDescription: "xpath is `config.Groups.{{kid.name|capitalize}}.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}`",
	    },
	    {%- endif %}
	    {# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty' %}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": schema.BoolAttribute{
		    Optional: true,
		    MarkdownDescription: "xpath is `config.Groups.{{kid.name|capitalize}}.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}`",
	    },
	    {%- endif %} #}
	    {%- if kid['type'] == 'list' or kid['type'] == 'container' %}
	    "{{kid.name|replace("-", "_")|replace(".", "_")}}": schema.ListNestedAttribute{
		    Optional: true,
		    NestedObject: schema.NestedAttributeObject{
			    Attributes: {{get_full_parent_name(kid, "_", 'True')}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.Attributes(),
	        },
        },
	    {%- endif %}
	    {%- endfor %}
    }
}
{%- endfor %}
{%- if arg2|length > 0 %}
{{create_struct(arg2, arg3)}}
{%- endif %}
{%- endif %}
{%- endmacro %}

// Collecting objects from the .tf file
type Groups_Model struct {
	ResourceName	types.String `tfsdk:"resource_name"`
	{%- for parent in parent_list %}
	{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} types.List `tfsdk:"{{parent.name|replace("-", "_")}}"`
	{%- endfor %}
}
func (o Groups_Model) AttrTypes() map[string]attr.Type {
	return map[string]attr.Type {
		{%- for parent in parent_list %}
		"{{parent.name|replace("-", "_")}}": 	types.ListType{ElemType: types.ObjectType{AttrTypes: {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.AttrTypes()}},
		{%- endfor %}
	}
}
func (o Groups_Model) Attributes() map[string]schema.Attribute {
	return map[string]schema.Attribute{
		"resource_name": schema.StringAttribute {
			Required: true,
			MarkdownDescription: "xpath is `config.Groups.resource_name`",
		},
		{%- for parent in parent_list %}
		"{{parent.name|replace("-", "_")}}": schema.ListNestedAttribute{
			Optional: true,
			NestedObject: schema.NestedAttributeObject{
				Attributes: {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.Attributes(),
			},
		},
		{%- endfor %}
	}
}

{%- for parent in parent_list %}
type {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model struct {
	{%- for kid in parent['kids']%}
	{%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}	types.String `tfsdk:"{{kid.name|replace("-", "_")}}"`
	{%- endif %}
	{# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} types.Bool `tfsdk:"{{kid.name|replace("-", "_")}}"`
	{%- endif %} #}
	{%- if kid['type'] == 'list' or kid['type']== 'container'%}
	{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}	types.List `tfsdk:"{{kid.name|replace("-", "_")}}"`
	{%- if ele_for_struct.append(kid) %} {% endif %}
	{%- endif %}
	{%- endfor %}
}
func (o {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model) AttrTypes() map[string]attr.Type {
	return map[string]attr.Type{
		{%- for kid in parent['kids']%}
		{%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
		"{{kid.name|replace("-", "_")}}": 	types.StringType,
		{%- endif %}
		{# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
		"{{kid.name|replace("-","_")}}": 	types.BoolType,
		{%- endif %} #}
		{%- if kid['type'] == 'list' or kid['type'] == 'container'%}
		"{{kid.name|replace("-", "_")}}": 	types.ListType{ElemType: types.ObjectType{AttrTypes: {{get_full_parent_name(kid, "_", "True")}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.AttrTypes()}},
		{%- endif %}
		{%- endfor %}
	}
}
func (o {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model) Attributes() map[string]schema.Attribute {
	return map[string]schema.Attribute{
		{%- for kid in parent['kids']%}
		{%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] ==  'empty' or kid['type'] == 'empty'%}
		"{{kid.name|replace("-", "_")}}": schema.StringAttribute{
			Optional: true,
			MarkdownDescription: "xpth is `config.Groups.{{parent.name|capitalize}}.{{kid.name|capitalize}}",
		},
		{%- endif %}
		{# {%- if kid['leaf-type'] ==  'empty' or kid['type'] == 'empty'%}
		"{{kid.name|replace("-","_")}}":schema.BoolAttribute{
			Optional: true,
			MarkdownDescription: "xpath is `config.Groups.{{parent.name|capitalize}}.{{kid.name|capitalize|replace("-","_")}}",
		},
		{%- endif %} #}
		{%- if (kid['type'] == 'list') or (kid['type'] == 'container') %}
		"{{kid.name|replace("-", "_")}}": schema.ListNestedAttribute{
			Optional: true,
			NestedObject: schema.NestedAttributeObject{
				Attributes: {{get_full_parent_name(kid, "_", "True")}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.Attributes(),
			},
		},
		{%- endif %}
		{%- endfor %}
	}
}
{%- endfor %}
{%- if ele_for_struct|length > 0 %}
{{create_struct(ele_for_struct, arg2)}}
{%- endif %}
{################ STRUCT FROM TF # ENDS ###############}

{################ SCHEMA DEFINITION # STARTS ###########}
// Collects the data for the crud work
type resource_Apply_Groups struct {
	client ProviderConfig
}

func (r *resource_Apply_Groups) Configure(_ context.Context, req resource.ConfigureRequest, _ *resource.ConfigureResponse) {
	if req.ProviderData == nil {
		return
	}
	r.client = req.ProviderData.(ProviderConfig)
}
// Metadata implements resource.Resource.
func (r *resource_Apply_Groups) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
	resp.TypeName = req.ProviderTypeName + "_Apply_Groups"
}
// Schema implements resource.Resource.
func (r *resource_Apply_Groups) Schema(_ context.Context, req resource.SchemaRequest, resp *resource.SchemaResponse) {
	resp.Schema = schema.Schema{
		Attributes: map[string]schema.Attribute{
			"resource_name": schema.StringAttribute{
				Required:      true,
				PlanModifiers: []planmodifier.String{stringplanmodifier.RequiresReplace()},
			},
			{%- for parent in parent_list %}
			"{{parent.name|replace("-", "_")}}": schema.ListNestedAttribute{
				Optional: true,
				NestedObject: schema.NestedAttributeObject{
					Attributes: {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.Attributes(),
				},
			},
			{%- endfor %}
		},
	}
}
{###################### SCHEMA DEFINITION # ENDS ###############}

{####################### CREATE METHOD # STARTS ################}

{%- macro create_method_macro(ele) %}
	    config.Groups.{{get_parent_list_with_iterator(ele)}}.{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}} = make([]xml_{{get_full_parent_name(ele, "_", "True")}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}, len(var_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}))
        for i_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}, v_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}} := range var_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}} {
            {%- for kid in ele['kids']%}
            {%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
            config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueStringPointer()
            {%- endif %}
            {# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
            if v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueBool() {
                empty := ""
                config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = &empty
            }
            {%- endif %} #}
            {%- if kid['type'] == 'list' or kid['type'] == 'container'%}
            var var_{{get_full_parent_name(kid, "_")}}_{{kid.name|replace("-", "_")|replace(".", "_")}} []{{get_full_parent_name(kid, "_", 'True')}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
            resp.Diagnostics.Append(v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ElementsAs(ctx, &var_{{get_full_parent_name(kid, "_")}}_{{kid.name|replace("-", "_")|replace(".", "_")}}, false)...)
            if resp.Diagnostics.HasError() {
                return
            }
                {{-create_method_macro(kid)}}
            {%- endif %}
            {%- endfor %}
        }
{%- endmacro %}

// Create implements resource.Resource.
func (r *resource_Apply_Groups) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
	
	var plan Groups_Model
	resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
	// Check for errors
	if resp.Diagnostics.HasError() {
		return
	}
	var config xml_Configuration
	config.Groups.Name = plan.ResourceName.ValueStringPointer()
    
	{% for parent in parent_list %}
    var var_{{parent.name|replace("-", "_")}} []{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
    if plan.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}.IsNull() {
        var_{{parent.name|replace("-", "_")}} = []{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}
    }else {
        resp.Diagnostics.Append(plan.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}.ElementsAs(ctx, &var_{{parent.name|replace("-", "_")}}, false)...)
        if resp.Diagnostics.HasError() {
            return
        }
    }
    config.Groups.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} = make([]xml_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}, len(var_{{parent.name|replace("-", "_")}}))
   
    for i_{{parent.name|replace("-", "_")}}, v_{{parent.name|replace("-", "_")}} := range var_{{parent.name|replace("-", "_")}} {
        {%- for kid in parent['kids']%}
        {%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid ['type'] == 'empty'%}
        config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueStringPointer()
        {%- endif %}
		{# {%- if kid['leaf-type'] == 'empty' or kid ['type'] == 'empty'%}
        if v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueBool() {
            empty := ""
            config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = &empty
        }
        {%- endif %} #}
        {%- if kid['type'] == 'container' or kid['type']== 'list'%}
        var var_{{parent.name|replace("-", "_")}}_{{kid.name|replace("-", "_")}} []{{get_full_parent_name(kid, "_", 'True')}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
        resp.Diagnostics.Append(v_{{parent.name|replace("-", "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ElementsAs(ctx, &var_{{parent.name|replace("-", "_")}}_{{kid.name|replace("-", "_")}}, false)...)
        if resp.Diagnostics.HasError() {
            return
        }
		{{-create_method_macro(kid)}}
        {%- endif %}
        {%- endfor %}
    }
	{% endfor %}
	err := r.client.SendTransaction(plan.ResourceName.ValueString(), config, false)
	if err != nil {
		resp.Diagnostics.AddError("Failed while adding group", err.Error())
		return
	}
	commit_err := r.client.SendCommit()
	if commit_err != nil {
		resp.Diagnostics.AddError("Failed while committing apply-group", commit_err.Error())
		return
	}
	resp.Diagnostics.Append(resp.State.Set(ctx, &plan)...)
}
{#################### CREATE METHOD # ENDS ################}

{############ READ METHOD # STARTS ################}

{%- macro read_method_macro(ele) %}
        {{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_List := make([]{{get_full_parent_name(ele, "_", 'True')}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model, len(v_{{get_full_parent_name(ele, "_")}}.{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}))
        for i_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}, v_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}} := range v_{{get_full_parent_name(ele, "_")}}.{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}} {
            var {{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_model {{get_full_parent_name(ele, "_", "True")}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
            {%- for kid in ele['kids'] %}
            {%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
            {{get_full_parent_name(ele,"_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_model.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = types.StringPointerValue(v_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}})
            {%- endif %}
            {# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
            {{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")}}_model.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = types.BoolValue(v_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} != nil)
            {%- endif %} #}
            {{get_full_parent_name(ele,"_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_List[i_{{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}] = {{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_model
            {%- if kid['type'] == 'list' or kid['type'] == 'container'%}
                {{read_method_macro(kid)}}
            {%- endif %}
            {%- endfor %}
        }
        {{get_full_parent_name(ele, "_")}}_model.{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}, _ = types.ListValueFrom(ctx, types.ObjectType{AttrTypes: {{get_full_parent_name(ele, "_", 'True')}}_{{ele.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.AttrTypes()}, {{get_full_parent_name(ele, "_")}}_{{ele.name|replace("-", "_")|replace(".", "_")}}_List)
        {{get_full_parent_name(ele, "_")}}_List[i_{{get_full_parent_name(ele, "_")}}] = {{get_full_parent_name(ele, "_")}}_model
{%- endmacro %}

func (r *resource_Apply_Groups) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
    
    var state Groups_Model
    resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
    if resp.Diagnostics.HasError() {
        return
    }

    var config xml_Configuration
    err := r.client.MarshalGroup(state.ResourceName.ValueString(), &config)
    if err != nil {
        resp.Diagnostics.AddError("Failed to read group", err.Error())
        return
    }
    {%- for parent in parent_list %}
    state.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} = types.ListNull(types.ObjectType{AttrTypes: Groups_Model{}.AttrTypes()})
    {{parent.name|replace("-", "_")}}_List := make([]{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model, len(config.Groups.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}))
    for i_{{parent.name|replace("-", "_")}}, v_{{parent.name|replace("-", "_")}} := range config.Groups.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} {
        var {{parent.name|replace("-", "_")}}_model {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
        {%- for kid in parent['kids'] %}
        {%- if kid['type'] == 'list' or kid['type'] == 'container'%}
            {{- read_method_macro(kid)}}
        {%- endif %}
        {%- endfor %}
    }
    state.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}, _ = types.ListValueFrom(ctx, types.ObjectType{AttrTypes: {{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}.AttrTypes()}, {{parent.name|replace("-", "_")}}_List)
	resp.Diagnostics.Append(resp.State.Set(ctx, &state)...)
    {%- endfor %} 
}

{############ READ METHOD # ENDS ################}

{################ UPDATE METHOD # STARTS #############}

// Update implements resource.Resource.
func (r *resource_Apply_Groups) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
	
	var plan Groups_Model
	resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
	// Check for errors
	if resp.Diagnostics.HasError() {
		return
	}
	var config xml_Configuration
	config.Groups.Name = plan.ResourceName.ValueStringPointer()
    
	{% for parent in parent_list %}
    var var_{{parent.name|replace("-", "_")}} []{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
    if plan.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}.IsNull() {
        var_{{parent.name|replace("-", "_")}} = []{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model{}
    }else {
        resp.Diagnostics.Append(plan.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}.ElementsAs(ctx, &var_{{parent.name|replace("-", "_")}}, false)...)
        if resp.Diagnostics.HasError() {
            return
        }
    }
    config.Groups.{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}} = make([]xml_{{parent.name|capitalize|replace("-", "_")|replace(".", "_")}}, len(var_{{parent.name|replace("-", "_")}}))
    
    for i_{{parent.name|replace("-", "_")}}, v_{{parent.name|replace("-", "_")}} := range var_{{parent.name|replace("-", "_")}} {
        {%- for kid in parent['kids']%}
        {%- if kid['leaf-type'] == 'string' or kid['base-type'] == 'string' or kid['leaf-type'] == 'union' or kid['type']== 'leaf-list' or kid['leaf-type']== 'enumeration' or kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
        config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueStringPointer()
        {%- endif %}
		{# {%- if kid['leaf-type'] == 'empty' or kid['type'] == 'empty'%}
        if v_{{get_full_parent_name(kid, "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ValueBool() {
            empty := ""
            config.Groups.{{get_parent_list_with_iterator(kid)}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}} = &empty
        }
        {%- endif %} #}
        {%- if kid['type'] == 'container' or kid['type']== 'list'%}
        var var_{{parent.name|replace("-", "_")}}_{{kid.name|replace("-", "_")}} []{{get_full_parent_name(kid, "_", 'True')}}_{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}_Model
        resp.Diagnostics.Append(v_{{parent.name|replace("-", "_")}}.{{kid.name|capitalize|replace("-", "_")|replace(".", "_")}}.ElementsAs(ctx, &var_{{parent.name|replace("-", "_")}}_{{kid.name|replace("-", "_")}}, false)...)
        if resp.Diagnostics.HasError() {
            return
        }
		{{-create_method_macro(kid)}}
        {%- endif %}
        {%- endfor %}
    }
	{% endfor %}
	err := r.client.SendTransaction(plan.ResourceName.ValueString(), config, false)
	if err != nil {
		resp.Diagnostics.AddError("Failed while Sending", err.Error())
		return
	}
	commit_err := r.client.SendCommit()
	if commit_err != nil {
		resp.Diagnostics.AddError("Failed while committing apply-group", commit_err.Error())
		return
	}
	resp.Diagnostics.Append(resp.State.Set(ctx, &plan)...)
}
{################## UPDATE METHOD # ENDS ################}

{################## DELETE METHOD # STARTS ################}
// Delete implements resource.Resource.
func (r *resource_Apply_Groups) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
	var state Groups_Model
	d := req.State.Get(ctx, &state)
	resp.Diagnostics.Append(d...)
	if resp.Diagnostics.HasError() {
		return
	}

	_, err := r.client.DeleteConfig(state.ResourceName.ValueString(), false)
	if err != nil {
		if strings.Contains(err.Error(), "ound") {
			return
		}
		resp.Diagnostics.AddError("Failed while deleting configuration", err.Error())
		return
	}
    commit_err := r.client.SendCommit()
	if commit_err != nil {
		resp.Diagnostics.AddError("Failed while committing apply-group", commit_err.Error())
		return
	}
	resp.Diagnostics.Append(resp.State.Set(ctx, &state)...)
}
{################## DELETE METHOD # ENDS ################}
    """
    tmpl = Template(jinja_source)
    return tmpl.render(data=data)
