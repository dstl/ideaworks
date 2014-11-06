dumpObjectIndented = (obj, indent="", isProp=false) ->

  isArray = obj instanceof Array
  isObject = typeof obj is "object" and not isArray
  isString = typeof obj is "string"
  isNumber = typeof obj is "number"
  isBoolean = typeof obj is "boolean"

  if isString
    out = '"' + obj + '"'
    if isProp
      return out
    else
      return indent + out
  if isNumber or isBoolean
    if isProp
      return obj
    else
      return indent + obj
  if isObject
    result = ""
    for own property, value of obj
      value = dumpObjectIndented(value, indent + "  ", true)
      result += indent + "'" + property + "' : " + value + ",\n"

    out = "{\n"
    out += result
    out += indent[2..]
    out += "}"
    if not isProp
      out = indent + out
  if isArray
    if obj.length is 0
      out = "[]"
    else if obj.length is 1
      out = "["+dumpObjectIndented(obj[0], indent + "  ", true)+"]"
    else
      ods = (dumpObjectIndented(item, indent + "  ")+"\n" for item in obj)
      out = "[ \n" + ods + "\n"+"]\n"

  out = out.replace(/\n,/g, ",\n")
  out = out.replace(/\n\n/g, "\n")
  return out


class ResourceFieldModel extends Backbone.Model


class ResourceFieldView extends Backbone.View

  initialize : (options) ->
    @template = _.template($("#resource_field_template").html())

  render : ->
    data = @model.toJSON()
    $(@el).html $(@template(data))
    return this


class SampleModel extends Backbone.Model

  url: ()->
      return @resource.get("list_endpoint")+"example/"


class ResourceModel extends Backbone.Model

  initialize : (options) =>
    @sample = new SampleModel()
    @sample.resource = this
    @bind('change', @refreshFieldList)
    super(options)

  refreshFieldList: ()->
    @fields = []
    resourceFiltering = @get("filtering") or {}
    for fieldName, fieldData of @get("fields")
      fieldData.default_value = fieldData.default
      fieldData.name = fieldName
      fieldData.filtering = resourceFiltering[fieldName] or []
      fieldData.filtering = [fieldData.filtering] if typeof fieldData.filtering == "string"
      @fields.push new ResourceFieldModel(fieldData)

  url: ()->
      @get("schema")

  loaded : ->
    return  @.toJSON()['fields'] isnt undefined

class ResourceView extends Backbone.View
  el: "#resource"

  initialize : (options) ->
    _.bindAll(@, 'render')
    @model or= new ResourceModel()
    @model.bind('change',@render)
    @template = _.template($("#resource_template").html())

  render : ->
    if not @model or not @model.loaded()
      return this

    $(@el).empty().html(@template(@model.toJSON()))
    fieldCompare = (aObj,bObj)->
        a = aObj.get("name")
        b = bObj.get("name")
        return -1 if a < b
        return  0 if a == b
        return  1 if a > b

    for field in @model.fields.sort fieldCompare
      fieldView = new ResourceFieldView(model: field)
      fieldView.render()
      @$(".field_list").append($(fieldView.el).html())

    @model.sample?.fetch
        success: @renderSample
        error: ()=>
            @model.sample.set {GET: "", POST: ""}
            @renderSample

    return this

  renderSample: ()=>
    @$("#examples").empty()
    template = _.template($("#example_template").html())
    for method in ['GET', 'POST']
        example = @formatExampleData(method, @model.sample.get(method))
        @$('#examples').append template( {method: method, example: example} )
    SyntaxHighlighter.highlight()


  formatExampleData : (method, data) ->
    method = method.toLowerCase()
    method_is_allowed   = method in @model.get("allowed_detail_http_methods")
    method_is_allowed or= method in @model.get("allowed_list_http_methods")

    if method_is_allowed and data?
      return dumpObjectIndented data
    else
      return "// not allowed"


class ResourceList extends Backbone.Collection
  url : ()->
      return window.api_url

  parse: (response)->
      ( new ResourceModel( _.extend(props, name: name) ) for name, props of response )


class ResourceListView extends Backbone.View
  el:   "#resource_list"
  events:
      "click .button": "showResource"

  initialize: ->
    _.bindAll(@,'render')
    @collection.bind('reset',@render)
    @template = _.template($("#resource_list_template").html())
    @resourceView = new ResourceView()

  render : ->
    $(@el).empty().append @template( collection: @collection )
    return @

  showResource: (event)->
      model_index = $(event.currentTarget).attr("data-index")
      @resourceView.model = @collection.at(model_index)
      @resourceView.model.fetch success: ()=> @resourceView.render()


$(document).ready ->
  resourcesView = new ResourceListView collection: new ResourceList()
  resourcesView.collection.fetch()
  window.resourcesView = resourcesView
