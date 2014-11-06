(function() {
  var ResourceFieldModel, ResourceFieldView, ResourceList, ResourceListView, ResourceModel, ResourceView, SampleModel, dumpObjectIndented;
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; }, __indexOf = Array.prototype.indexOf || function(item) {
    for (var i = 0, l = this.length; i < l; i++) {
      if (this[i] === item) return i;
    }
    return -1;
  };
  dumpObjectIndented = function(obj, indent, isProp) {
    var isArray, isBoolean, isNumber, isObject, isString, item, ods, out, property, result, value;
    if (indent == null) {
      indent = "";
    }
    if (isProp == null) {
      isProp = false;
    }
    isArray = obj instanceof Array;
    isObject = typeof obj === "object" && !isArray;
    isString = typeof obj === "string";
    isNumber = typeof obj === "number";
    isBoolean = typeof obj === "boolean";
    if (isString) {
      out = '"' + obj + '"';
      if (isProp) {
        return out;
      } else {
        return indent + out;
      }
    }
    if (isNumber || isBoolean) {
      if (isProp) {
        return obj;
      } else {
        return indent + obj;
      }
    }
    if (isObject) {
      result = "";
      for (property in obj) {
        if (!__hasProp.call(obj, property)) continue;
        value = obj[property];
        value = dumpObjectIndented(value, indent + "  ", true);
        result += indent + "'" + property + "' : " + value + ",\n";
      }
      out = "{\n";
      out += result;
      out += indent.slice(2);
      out += "}";
      if (!isProp) {
        out = indent + out;
      }
    }
    if (isArray) {
      if (obj.length === 0) {
        out = "[]";
      } else if (obj.length === 1) {
        out = "[" + dumpObjectIndented(obj[0], indent + "  ", true) + "]";
      } else {
        ods = (function() {
          var _i, _len, _results;
          _results = [];
          for (_i = 0, _len = obj.length; _i < _len; _i++) {
            item = obj[_i];
            _results.push(dumpObjectIndented(item, indent + "  ") + "\n");
          }
          return _results;
        })();
        out = "[ \n" + ods + "\n" + "]\n";
      }
    }
    out = out.replace(/\n,/g, ",\n");
    out = out.replace(/\n\n/g, "\n");
    return out;
  };
  ResourceFieldModel = (function() {
    __extends(ResourceFieldModel, Backbone.Model);
    function ResourceFieldModel() {
      ResourceFieldModel.__super__.constructor.apply(this, arguments);
    }
    return ResourceFieldModel;
  })();
  ResourceFieldView = (function() {
    __extends(ResourceFieldView, Backbone.View);
    function ResourceFieldView() {
      ResourceFieldView.__super__.constructor.apply(this, arguments);
    }
    ResourceFieldView.prototype.initialize = function(options) {
      return this.template = _.template($("#resource_field_template").html());
    };
    ResourceFieldView.prototype.render = function() {
      var data;
      data = this.model.toJSON();
      $(this.el).html($(this.template(data)));
      return this;
    };
    return ResourceFieldView;
  })();
  SampleModel = (function() {
    __extends(SampleModel, Backbone.Model);
    function SampleModel() {
      SampleModel.__super__.constructor.apply(this, arguments);
    }
    SampleModel.prototype.url = function() {
      return this.resource.get("list_endpoint") + "example/";
    };
    return SampleModel;
  })();
  ResourceModel = (function() {
    __extends(ResourceModel, Backbone.Model);
    function ResourceModel() {
      this.initialize = __bind(this.initialize, this);
      ResourceModel.__super__.constructor.apply(this, arguments);
    }
    ResourceModel.prototype.initialize = function(options) {
      this.sample = new SampleModel();
      this.sample.resource = this;
      this.bind('change', this.refreshFieldList);
      return ResourceModel.__super__.initialize.call(this, options);
    };
    ResourceModel.prototype.refreshFieldList = function() {
      var fieldData, fieldName, resourceFiltering, _ref, _results;
      this.fields = [];
      resourceFiltering = this.get("filtering") || {};
      _ref = this.get("fields");
      _results = [];
      for (fieldName in _ref) {
        fieldData = _ref[fieldName];
        fieldData.default_value = fieldData["default"];
        fieldData.name = fieldName;
        fieldData.filtering = resourceFiltering[fieldName] || [];
        if (typeof fieldData.filtering === "string") {
          fieldData.filtering = [fieldData.filtering];
        }
        _results.push(this.fields.push(new ResourceFieldModel(fieldData)));
      }
      return _results;
    };
    ResourceModel.prototype.url = function() {
      return this.get("schema");
    };
    ResourceModel.prototype.loaded = function() {
      return this.toJSON()['fields'] !== void 0;
    };
    return ResourceModel;
  })();
  ResourceView = (function() {
    __extends(ResourceView, Backbone.View);
    function ResourceView() {
      this.renderSample = __bind(this.renderSample, this);
      ResourceView.__super__.constructor.apply(this, arguments);
    }
    ResourceView.prototype.el = "#resource";
    ResourceView.prototype.initialize = function(options) {
      _.bindAll(this, 'render');
      this.model || (this.model = new ResourceModel());
      this.model.bind('change', this.render);
      return this.template = _.template($("#resource_template").html());
    };
    ResourceView.prototype.render = function() {
      var field, fieldCompare, fieldView, _i, _len, _ref, _ref2;
      if (!this.model || !this.model.loaded()) {
        return this;
      }
      $(this.el).empty().html(this.template(this.model.toJSON()));
      fieldCompare = function(aObj, bObj) {
        var a, b;
        a = aObj.get("name");
        b = bObj.get("name");
        if (a < b) {
          return -1;
        }
        if (a === b) {
          return 0;
        }
        if (a > b) {
          return 1;
        }
      };
      _ref = this.model.fields.sort(fieldCompare);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        field = _ref[_i];
        fieldView = new ResourceFieldView({
          model: field
        });
        fieldView.render();
        this.$(".field_list").append($(fieldView.el).html());
      }
      if ((_ref2 = this.model.sample) != null) {
        _ref2.fetch({
          success: this.renderSample,
          error: __bind(function() {
            this.model.sample.set({
              GET: "",
              POST: ""
            });
            return this.renderSample;
          }, this)
        });
      }
      return this;
    };
    ResourceView.prototype.renderSample = function() {
      var example, method, template, _i, _len, _ref;
      this.$("#examples").empty();
      template = _.template($("#example_template").html());
      _ref = ['GET', 'POST'];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        method = _ref[_i];
        example = this.formatExampleData(method, this.model.sample.get(method));
        this.$('#examples').append(template({
          method: method,
          example: example
        }));
      }
      return SyntaxHighlighter.highlight();
    };
    ResourceView.prototype.formatExampleData = function(method, data) {
      var method_is_allowed;
      method = method.toLowerCase();
      method_is_allowed = __indexOf.call(this.model.get("allowed_detail_http_methods"), method) >= 0;
      method_is_allowed || (method_is_allowed = __indexOf.call(this.model.get("allowed_list_http_methods"), method) >= 0);
      if (method_is_allowed && (data != null)) {
        return dumpObjectIndented(data);
      } else {
        return "// not allowed";
      }
    };
    return ResourceView;
  })();
  ResourceList = (function() {
    __extends(ResourceList, Backbone.Collection);
    function ResourceList() {
      ResourceList.__super__.constructor.apply(this, arguments);
    }
    ResourceList.prototype.url = function() {
      return window.api_url;
    };
    ResourceList.prototype.parse = function(response) {
      var name, props, _results;
      _results = [];
      for (name in response) {
        props = response[name];
        _results.push(new ResourceModel(_.extend(props, {
          name: name
        })));
      }
      return _results;
    };
    return ResourceList;
  })();
  ResourceListView = (function() {
    __extends(ResourceListView, Backbone.View);
    function ResourceListView() {
      ResourceListView.__super__.constructor.apply(this, arguments);
    }
    ResourceListView.prototype.el = "#resource_list";
    ResourceListView.prototype.events = {
      "click .button": "showResource"
    };
    ResourceListView.prototype.initialize = function() {
      _.bindAll(this, 'render');
      this.collection.bind('reset', this.render);
      this.template = _.template($("#resource_list_template").html());
      return this.resourceView = new ResourceView();
    };
    ResourceListView.prototype.render = function() {
      $(this.el).empty().append(this.template({
        collection: this.collection
      }));
      return this;
    };
    ResourceListView.prototype.showResource = function(event) {
      var model_index;
      model_index = $(event.currentTarget).attr("data-index");
      this.resourceView.model = this.collection.at(model_index);
      return this.resourceView.model.fetch({
        success: __bind(function() {
          return this.resourceView.render();
        }, this)
      });
    };
    return ResourceListView;
  })();
  $(document).ready(function() {
    var resourcesView;
    resourcesView = new ResourceListView({
      collection: new ResourceList()
    });
    resourcesView.collection.fetch();
    return window.resourcesView = resourcesView;
  });
}).call(this);
