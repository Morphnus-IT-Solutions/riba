<?php
header("Cache-Control: no-cache, must-revalidate");
header("Expires: Mon, 26 Jul 1997 05:00:00 GMT");

$host="localhost";
$username="";
$password="";
$database="sample";

$con=mysql_connect($host,$username,$password) or die(mysql_error());
mysql_select_db($database,$con) or die(mysql_error());

$arr=array();
$result=mysql_query("SELECT * FROM sample WHERE title LIKE '%".mysql_real_escape_string($_GET['chars'])."%' LIMIT 0, 10",$con) or die(mysql_error());
if(mysql_num_rows($result)>0){
    while($data=mysql_fetch_row($result)){
        // Store data in array
        $arr[]=$data[1];
    }
}

mysql_close($con);

// Encode it with JSON format
echo json_encode($arr);
?>