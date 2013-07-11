<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
    <title>DIRAC :: DESKTOP</title>
	<link rel="SHORTCUT ICON" href='/DIRAC/static/core/img/icons/system/favicon.ico'>
    <link rel="stylesheet" type="text/css" href="/DIRAC/static/extjs/{{ext_version}}/resources/css/{{theme}}.css" />
    <link rel="stylesheet" type="text/css" href="/DIRAC/static/core/css/css.css" />
    {% autoescape None %}
    <!-- GC -->

    <!-- <x-compile> -->
    <!-- <x-bootstrap> -->

    {% if _dev %}
      <script type="text/javascript" src="/DIRAC/static/extjs/{{ext_version}}/ext-all.js"></script>
    {% else %}
      <script type="text/javascript" src="/DIRAC/static/core/build/all-classes.js"></script>
    {% end %}
    <!-- </x-bootstrap> -->
    <script type="text/javascript">
    {% if _dev %}
          Ext.Loader.setPath({
      {% for extName in extensions %}
        {% if extName != 'WebAppDIRAC' %}
            {{ escape( extName ) }}: "{{ escape( '/DIRAC/static/%s' % ( extName ) ) }}",
        {% end %}
      {% end %}
            'Ext.dirac.core': '/DIRAC/static/core/js/core',
            'Ext.dirac.utils': '/DIRAC/static/core/js/utils',
            'Ext.ux.form':'/DIRAC/static/extjs/{{ext_version}}/examples/ux/form'
          });

          Ext.require(['Ext.dirac.core.App','Ext.*']);
		  
		  var GLOBAL = {};
		  	
          GLOBAL.APP = null;
          GLOBAL.BASE_URL = "";
          GLOBAL.EXTJS_VERSION = "{{ext_version}}";
          GLOBAL.DEV = 1;
          GLOBAL.URL_STATE = "{{url_state}}";
          GLOBAL.MOUSE_X = 0;
          GLOBAL.MOUSE_Y = 0;
          GLOBAL.IS_IE = false;
          {% import json %}
          GLOBAL.USER_CREDENTIALS = {{ json.dumps( credentials ) }}; 
          GLOBAL.WEB_THEME = "{{theme}}";
          GLOBAL.STATE_MANAGEMENT_ENABLED = true;

          Ext.onReady(function () {
            	GLOBAL.BASE_URL = "{{base_url}}/";
              	GLOBAL.APP = new Ext.dirac.core.App();
              	setTimeout(function(){
                	Ext.get("app-dirac-loading").hide();
                	Ext.get("app-dirac-loading-msg").setHTML("Loading module. Please wait ...");
              	},1000);
          });
      {% else %}
      	  var GLOBAL = {};
		  	
          GLOBAL.APP = null;
          GLOBAL.BASE_URL = "";
          GLOBAL.EXTJS_VERSION = "{{ext_version}}";
          GLOBAL.DEV = 0;
          GLOBAL.URL_STATE = "{{url_state}}";
          GLOBAL.MOUSE_X = 0;
          GLOBAL.MOUSE_Y = 0;
          GLOBAL.IS_IE = false;
          {% import json %}
          GLOBAL.USER_CREDENTIALS = {{ json.dumps( credentials ) }};
          GLOBAL.WEB_THEME = "{{theme}}"; 
          GLOBAL.STATE_MANAGEMENT_ENABLED = true;
      
          Ext.onReady(function () {
              GLOBAL.BASE_URL = "{{base_url}}/";
              GLOBAL.APP = new Ext.dirac.core.App();
              setTimeout(function(){
                Ext.get("app-dirac-loading").hide();
                Ext.get("app-dirac-loading-msg").setHTML("Loading module. Please wait ...");
              },1000);
          });
      {% end %}
    </script>
    <!-- </x-compile> -->
</head>

<body>
  <div id="app-dirac-loading">
      <div class="app-dirac-loading-indicator">
        <table>
          <tr>
            <td style="width:100px;">
              <img src="/DIRAC/static/core/img/icons/system/_logo_waiting.gif" style="margin-right:8px;float:left;vertical-align:top;width:100%;"/>
            </td>
            <td style="width:200px;vertical-align:middle;text-align:left;padding:5px 0px 5px 15px;font-size:14px">
              DIRAC
                <br />
                <span id="app-dirac-loading-msg">Loading data and resources...</span>
            </td>
          </tr>
        </table>

      </div>
  </div>

</body>
</html>
