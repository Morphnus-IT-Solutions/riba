package gateways;


import org.apache.log4j.Logger;
import org.json.JSONObject;

import com.aciworldwide.commerce.gateway.plugins.*;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

import javax.servlet.http.HttpServletResponse;

public class TranPipeBuy {

	private static class SingletonHolder {
		private static final TranPipeBuy INSTANCE = new TranPipeBuy();
	}
	//private Logger gateway;

	private TranPipeBuy() {
		//gateway = Logger.getLogger("gateway");
		//gateway.info("HDFC gateway initialized");

	}

	public static TranPipeBuy getInstance() {

		return SingletonHolder.INSTANCE;
	}

	public JSONObject initiatePayment(JSONObject data, HttpServletResponse res) throws Exception {
		JSONObject o = new JSONObject();

		e24VbVPlugin pipe= new e24VbVPlugin();
		
		String name = data.getString("name");
		String currcd= data.optString("currcd",null);
		String expmm  = data.getString("expmm");
		String expyy  = data.getString("expyy");
		Random rnd = new Random(System.currentTimeMillis());
		String pan    = data.getString("pan");
		String cvv    = data.getString("cvv");
		String action = data.getString("pg_action");
		String mid = data.getString("gateway");
		String orderId = data.getString("orderId");
		String amount=data.getString("amount");
		String PARes = data.optString("PaRes",null);
		//gateway.info("input data" + data.toString());
		if(PARes == null) {
			if(mid.equalsIgnoreCase("hdfc-emi")){
				String emi_plan = data.getString("emi_plan");
				pipe.setAlias("72000199");
				pipe.setResourcePath("/home/chaupaati/hdfcres/HDF" + emi_plan + "/");
			}
			else{
				pipe.setResourcePath("/home/chaupaati/hdfcres/HDFC-CARD/");
				pipe.setAlias("70000213");
			}
			pipe.setAmt(amount);
			//session.setAttribute("amount",amount);
			pipe.setCurrency(currcd);
			pipe.setMember(name);

			pipe.setAction(action);
			//pipe.setTrackId(String.valueOf(Math.abs(rnd.nextLong())));
			pipe.setTrackId(orderId);
			pipe.setCVV2(cvv);
			pipe.setExpMonth(expmm);
			pipe.setExpYear(expyy);
			pipe.setExpDay(expmm);  // Sample
			pipe.setCard(pan);
			//pipe.setDebug(true);
			try{
				pipe.performVETransaction();
				//gateway.info("calling ... performVETransaction");
			}catch(NotEnoughDataException e){
				//gateway.info("NotEnoughDataException" + e.getMessage());
			}
			catch(Exception e1){
				//gateway.info(e1.getMessage());
			}
			
			String Pay_Id = pipe.getPaymentId();
			//gateway.info("result.." + pipe.getResult());

			if(pipe.getResult() != null) {
				if(pipe.getResult().equals("ENROLLED")) {
					//gateway.info("ACS URL" + pipe.getACSURL());
					Map<String, Object> out = new HashMap<String, Object>();
					out.put("redirectUrl", pipe.getACSURL());
					out.put("pareq", pipe.getPAReq());
					out.put("payment_id", pipe.getPaymentId());
					return new JSONObject(out);
					
				} else {   // Not Enrolled Starts
					if(pipe.getResult().equals("NOT ENROLLED")) {
						Map<String, Object> out = new HashMap<String, Object>();
						out.put("error", "NOT ENROLLED");
						return new JSONObject(out);
					} 
				}    // Not Enrolled Ends
			}
		} else {
			if(mid.equalsIgnoreCase("hdfc-emi")){
				String emi_plan = data.getString("emi_plan");
				pipe.setAlias("72000199");
				pipe.setResourcePath("/home/chaupaati/hdfcres/HDF" + emi_plan + "/");
			}
			else{
				pipe.setAlias("70000213");
				pipe.setResourcePath("/home/chaupaati/hdfcres/HDFC-CARD/");
	
			}
			pipe.setAuthToken("");


			pipe.setPaymentId(data.getString("MD"));
			pipe.setPARes(data.getString("PaRes"));

			pipe.performPATransaction();

			//out.println("RESULT --- " + pipe.getResult());

	}
		return o;
}
public JSONObject processPayment(JSONObject data) throws Exception{
		String PARes = data.optString("PaRes",null);
		String mid = data.getString("gateway");
		e24VbVPlugin pipe= new e24VbVPlugin();
		if(mid.equalsIgnoreCase("hdfc-emi")){
			String emi_plan = data.getString("emi_plan");
			pipe.setAlias("72000199");
			pipe.setResourcePath("/home/chaupaati/hdfcres/HDF" + emi_plan + "/");
		}
		else{
			pipe.setAlias("70000213");
			pipe.setResourcePath("/home/chaupaati/hdfcres/HDFC-CARD/");
		}
		pipe.setAuthToken("");

		pipe.setPaymentId(data.getString("MD"));
		pipe.setPARes(data.getString("PaRes"));

		short responseCode = pipe.performPATransaction();
		Map<String, Object> out = new HashMap<String, Object>();
		out.put("result", pipe.getResult());
		out.put("responseCode", responseCode);
		return new JSONObject(out);	
		
	}

}