package gateways;

import java.io.*;
import java.math.BigDecimal;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Hashtable;
import java.util.Locale;
import java.util.Map;
import java.util.StringTokenizer;

import javax.servlet.ServletOutputStream;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.apache.log4j.Logger;
import org.json.*;

import com.opus.*;
import com.opus.epg.*;
import com.opus.epg.sfa.*;
import com.opus.epg.sfa.java.*;

@SuppressWarnings("unused")
public class ICICIPayseal {
	private static class SingletonHolder {
		private static final ICICIPayseal INSTANCE = new ICICIPayseal();
	}

	private static final String MERCHANT_ID = "00004556";
	private static final String GMT_OFFSET = "GMT+05:30";
	DateFormat yyyyMMdd = new SimpleDateFormat("yyyyMMdd");
	private Logger gateway;

	private ICICIPayseal() {
		gateway = Logger.getLogger("gateway");

	}

	public static ICICIPayseal getInstance() {

		return SingletonHolder.INSTANCE;
	}

	public static String formatCurrency(long value, String currency)
	{
		return formatCurrency(value, currency, "");
	}

	public static String formatCurrency(long value, String currency, String dec)
	{
        StringBuffer sb = new StringBuffer(value + "");
        int len = sb.length();
        if (len < 4)
        {
        	if ( currency.equals("usd"))
            	return "$" + sb.toString() + dec;
            else if (currency.equals("inr"))
            	return "Rs. " + sb.toString() + dec;
            else if ( currency.equals("") )
            	return "Rs. " + sb.toString() + dec;
            return "Rs " + sb.toString() + dec;
        }
        int cp = len - 3;
        sb.insert(cp, ',');
        if (len < 6)
        {
        	if ( currency.equals("usd"))
            	return "$" + sb.toString() + dec;
            else if (currency.equals("inr"))
            	return "Rs. " + sb.toString() + dec;
            else if ( currency.equals("") )
            	return "Rs. " + sb.toString() + dec;
            return "Rs " + sb.toString() + dec;
        }

        while (cp > 2)
        {
                cp -= 2;
                sb.insert(cp, ',');
        }
        
        if ( currency.equals("usd"))
        	return "$" + sb.toString() + dec;
        else if (currency.equals("inr"))
        	return "Rs. " + sb.toString() + dec;
        else if ( currency.equals("") )
        	return "Rs. " + sb.toString() + dec;
        return "Rs. " + sb.toString() + dec;
	}
	
	public static String formatCurrency(long value)
	{
		return formatCurrency(value, "inr", "");
	}

	public static String formatCurrency(double amount, String currency) {
		String value = String.format("%.2f", amount);
		long x = 0;
		if(value.indexOf(".")!=-1) {
			x = Long.parseLong(value.split("\\.")[0]);
		}
		else
			x = Long.parseLong(value);
		
		String dec = "";
		if(value.indexOf(".")!=-1)
			dec = value.split("\\.")[1];
		String formatted = formatCurrency(x, currency, "."+dec);
		return formatted;
	}

	public JSONObject initiatePayment(JSONObject data, HttpServletResponse res) throws Exception {
		
		
		String currency = data.optString("currency","inr");
		String orderText = "Chaupaati Bazaar Order# ";
		
		PGResponse pgResponse = new PGResponse();
		CustomerDetails payee = new CustomerDetails();
		SessionDetail session = new SessionDetail();
		MerchanDise productInfo = new MerchanDise();
		PostLib postLib = new PostLib();
		
		CardInfo cardInfo = new CardInfo();
		Merchant merchant = new Merchant();

		ShipToAddress shippingAddress = new ShipToAddress();
		BillToAddress billingAddress = new BillToAddress();

		MPIData mpiData = new MPIData();
		PGReserveData pgReserveData = new PGReserveData();

		Address homeAddress = new Address();
		Address officeAddress = new Address();

		String paymentOrderId = "";
		
		String returnUrl = data.optString("returnUrl",
				"http://www.chaupaati.in/orders/process_payment");
		String ip = data.optString("ip", "10.10.10.108");
		boolean detectFraud = data.optBoolean("detectFraud", false);
		boolean storeBillingShipping = data.optBoolean("storeBillingShipping",
				false);
		String useragent = data
				.optString(
						"useragent",
						"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.15) Gecko/2009102814 Ubuntu/8.04 (hardy) Firefox/3.0.15");
		String acceptHeader = data
				.optString("acceptHeader",
						"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
		String reqType = data.optString("reqType", "req.Sale");
		String transactionId = data.getString("transactionId");
		String orderId = data.getString("orderId");
		double amount = data.getDouble("amount");
		merchant.setMerchantDetails(MERCHANT_ID, MERCHANT_ID, MERCHANT_ID, ip,
				transactionId, orderId, returnUrl, "POST", currency
						.toUpperCase(), orderId, reqType, String.format(
						"%.2f", amount), GMT_OFFSET, "", "", "", "", "");
		billingAddress = null;
		shippingAddress = null;
		
		session = null;
		homeAddress = null;
		officeAddress = null;
		payee = null;
		productInfo = null;

		mpiData.setMPIRequestDetails(String.format("%.2f", amount),
				this.formatCurrency(amount, currency),
				getISOCurrencyCode(currency), "2", orderText + orderId,
				"1", yyyyMMdd.format(Calendar.getInstance().getTime()), "1",
				"0", null, acceptHeader, useragent);

		pgResponse = postLib.postSSL(billingAddress, shippingAddress, merchant,
				null, null, pgReserveData, payee, session, null, null);
		if (pgResponse.getRedirectionUrl() != null) {
			gateway.info("redirectUrl for icici is "
					+ pgResponse.getRedirectionUrl());
			gateway.info("redirectionTxnId for icici is "
					+ pgResponse.getRedirectionTxnId());
			gateway.info("epgTxnId for icici is " + pgResponse.getEpgTxnId());
		}
		
		Map<String, Object> out = new HashMap<String, Object>();
		out.put("redirectUrl", pgResponse.getRedirectionUrl());
		return new JSONObject(out);
	}

	public JSONObject processPayment(JSONObject data) {
		
		String rawData = data.optString("rawData", "");
		String clearData = validateEncryptedData(rawData, "", MERCHANT_ID);
		Map<String, String> htable = new HashMap<String, String>();

		StringTokenizer oStringTokenizer = new StringTokenizer(clearData, "&");
		while (oStringTokenizer.hasMoreElements()) {
			String strData = (String) oStringTokenizer.nextElement();
			StringTokenizer oObj1 = new StringTokenizer(strData, "=");
			String strKey = (String) oObj1.nextElement();
			String strValue = (String) oObj1.nextElement();
			htable.put(strKey, strValue);
		}

		String respcd = htable.get("RespCode");
		String respmsg = ((String) htable.get("Message")).replace('+', ' ');
		String AuthIdCode = (String) htable.get("AuthIdCode");
		String RRN = (String) htable.get("RRN");
		String MerchantTxnId = (String) htable.get("TxnID");
		String TxnRefNo = (String) htable.get("ePGTxnID");
		String Cookie = (String) htable.get("Cookie");
		String FDMSResult = htable.get("FDMSResult");
		String FDMSScore = htable.get("FDMSScore");

		Map<String, Object> out = new HashMap<String, Object>();
		if (respcd.equalsIgnoreCase("0")) {
			out.put("status", "approved");
		} else {
			out.put("status", "pending");
		}
		return new JSONObject(out);

	}

	private String validateEncryptedData(String rawData, String keyDir,
			String merchantId) {
		EPGMerchantEncryptionLib oEncryptionLib = new EPGMerchantEncryptionLib();
		String astrClearData = null;
		try {
			FileInputStream oFileInputStream = new FileInputStream(new File(
					keyDir + merchantId + ".key"));
			BufferedReader oBuffRead = new BufferedReader(
					new InputStreamReader(oFileInputStream));
			String strModulus = oBuffRead.readLine();
			if (strModulus == null) {
				throw new SFAApplicationException(
						"Invalid credentials. Transaction cannot be processed");
			}
			strModulus = decryptMerchantKey(strModulus, merchantId);
			if (strModulus == null) {
				throw new SFAApplicationException(
						"Invalid credentials. Transaction cannot be processed");
			}
			String strExponent = oBuffRead.readLine();
			if (strExponent == null) {
				throw new SFAApplicationException(
						"Invalid credentials. Transaction cannot be processed");
			}
			strExponent = decryptMerchantKey(strExponent, merchantId);
			if (strExponent == null) {
				throw new SFAApplicationException(
						"Invalid credentials. Transaction cannot be processed");
			}
			astrClearData = oEncryptionLib.decryptDataWithPrivateKeyContents(
					rawData, strModulus, strExponent);

		} catch (Exception oEx) {
			oEx.printStackTrace();
		}
		return astrClearData;
	}

	private String decryptMerchantKey(String astrData, String astrMerchantId)
			throws Exception {
		return (decryptData(astrData, (astrMerchantId + astrMerchantId)
				.substring(0, 16)));
	}

	private String decryptData(String strData, String strKey) throws Exception {
		if (strData == null || strData == "") {
			return null;
		}
		if (strKey == null || strKey == "") {
			return null;
		}
		EPGCryptLib moEPGCryptLib = new EPGCryptLib();
		String strDecrypt = moEPGCryptLib.Decrypt(strKey, strData);
		return strDecrypt;
	}

	private String getISOCurrencyCode(String currency) {
		if (currency.toLowerCase().equals("inr"))
			return "356";
		if (currency.toLowerCase().equals("usd"))
			return "356";
		return "356";
	}
}
