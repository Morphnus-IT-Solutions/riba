<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
  <title>jQuery Plugin For Auto-Suggest</title>
  <script language="javascript" type="text/javascript" src="js/jquery.js"></script>
  <script language="javascript" type="text/javascript" src="js/jquery.suggestion.js"></script>
  <link rel="stylesheet" type="text/css" href="css/styles.css" />
</head>
<body>
  <p><b>JQuery Plugin For Ajax Auto-Suggest.</b></p>
  <form action="" method="post">
    <fieldset>
      <legend><b>Simple auto suggest textfield</b></legend>
      <p>The width of suggestions list is automatically adjusted to textfield's width.</p>
      Search : <input type="text" id="text1" />
      <script language="javascript" type="text/javascript">
	$("#text1").suggestion({
	  url:"data.php?chars="
	});
      </script>
    </fieldset>
    <br/>
    <fieldset>
      <legend><b>Auto suggest textfield with <i>minChars</i> and <i>width</i> options</b></legend>
      <p>Suggestions list will appear after 2 or more characters are typed. It also has a fixed width (200 pixel).</p>
      Search : <input type="text" id="text2" />
      <script language="javascript" type="text/javascript">
	$("#text2").suggestion({
	  url:"data.php?chars=",
	  minChars:2,
	  width:200
	});
      </script>
      <br/>
      <p><i>* If you try this example in Internet Explorer 6, the suggestions list will stay on top of combo box component.</i></p>
      Combobox :
      <select name="test">
	<option value="1">Sample option 1</option>
	<option value="2">Sample option 2</option>
	<option value="3">Sample option 3</option>
      </select>
    </fieldset>
  </form>
</body>
</html>