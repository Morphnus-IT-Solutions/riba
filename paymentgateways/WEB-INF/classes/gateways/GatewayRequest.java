package gateways;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Calendar;
import java.util.HashMap;

import javax.servlet.ServletException;
import javax.servlet.ServletInputStream;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.log4j.Logger;
import org.apache.log4j.NDC;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Servlet implementation class GatewayRequest
 */
public class GatewayRequest extends HttpServlet {
	private static final long serialVersionUID = 1L;
	private Logger gateway;
       
    /**
     * @see HttpServlet#HttpServlet()
     */
    public GatewayRequest() {
        super();
        //gateway = Logger.getLogger("gateway");
        // TODO Auto-generated constructor stub
    }

    private String getPostData(HttpServletRequest req) throws IOException
	{
		byte[] buffer = new byte[req.getContentLength()];
		int buflen = 0;
		int read = 0;

		ServletInputStream in = req.getInputStream();
		

		while( read > -1 ) {
			buflen += read;
			read = in.read(buffer, buflen, req.getContentLength() - buflen);
		}

		String charSetName = req.getCharacterEncoding();
		if( (charSetName == null) || (charSetName.equals("")) )
			charSetName = "utf-8";

		return new String(buffer, 0, buflen, charSetName);
	}

	/**
	 * @see HttpServlet#doGet(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doGet(HttpServletRequest req, HttpServletResponse response) throws ServletException, IOException {
	}

	/**
	 * @see HttpServlet#doPost(HttpServletRequest request, HttpServletResponse response)
	 */
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		PrintWriter out = response.getWriter();
		String user = "";
		user = request.getRemoteUser();
		StringBuilder url = new StringBuilder( "POST ");
		url.append( request.getRequestURI() ).append("?").append( request.getQueryString() );
		
		NDC.push( request.getRemoteAddr() + " - " + Calendar.getInstance().getTime().getTime() + " - " + user);

		String rawData ="";
		rawData = getPostData(request);
		//gateway.info( url.toString() + " with data : " + rawData );

		JSONObject data = null;
		JSONObject json = null;
		try {
			data = new JSONObject( rawData );
			String pg_gateway = data.getString("gateway");
			
			if (data.getString("action").equalsIgnoreCase("create_new")) {
				try {
					if (pg_gateway.equalsIgnoreCase("icici")){
						json = ICICIPayseal.getInstance().initiatePayment(data, response);
						out.println(json.toString());
					}
					if (pg_gateway.equalsIgnoreCase("hdfc-emi") || pg_gateway.equalsIgnoreCase("hdfc-card")){
						json = TranPipeBuy.getInstance().initiatePayment(data, response);
						out.println(json.toString());
					}
				
				} catch (Exception e) {
					System.out.print(e.getMessage());
					//gateway.error("error creating payment request " + e.getMessage(), e);
				}
			}
			if (data.getString("action").equalsIgnoreCase("process_payment")) {
				try {
					if(pg_gateway.equalsIgnoreCase("icici")){
						json = ICICIPayseal.getInstance().processPayment(data);
						out.println(json.toString());
					}
					if(pg_gateway.startsWith("hdfc")){
						json = TranPipeBuy.getInstance().processPayment(data);
						out.println(json.toString());
					}
				} catch (Exception e) {
					//gateway.error("error processing payment response " + e.getMessage(), e);
				}
			}
		}
		catch (JSONException j) {
			//gateway.error( url.toString() + " has badly formed JSON :\n" + rawData );	
		}
	}
}
