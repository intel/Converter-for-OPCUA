package com.intel.cfsdk.plugin.mqtt;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttMessage;

public class PushCallback implements MqttCallback {

	public void connectionLost(Throwable cause) {
		//System.out.println("reconnect");
	}

	public void deliveryComplete(IMqttDeliveryToken token) {
		//System.out.println("deliveryComplete------" + token.isComplete());
	}

	public void messageArrived(String topic, MqttMessage message) throws Exception {
		//System.out.println(" topic " + topic); 
		//System.out.println(" Qos" + message.getQos()); 
		//System.out.println(" content " + new String(message.getPayload())); 
	}

}
