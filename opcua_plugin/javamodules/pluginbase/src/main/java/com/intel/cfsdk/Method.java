package com.intel.cfsdk;

import java.util.HashMap;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONException;

public class Method {
    public String name = null;
    public List<JSONObject> inputParams=new ArrayList<JSONObject>();
    public int required = 0;

    public Method(String funcName, JSONArray inputs, JSONArray outputs) {
        String nodeType;
        String defaultVal = null;
        boolean hasDefault = false;
        this.name = funcName;
        this.required = 0;

        if(inputs == null){
            return;
        }

        for ( int loop = 0; loop < inputs.size(); loop++) {
            defaultVal = null;
            hasDefault = false;
            try {
                JSONObject object = inputs.getJSONObject(loop);
                if(object.containsKey("type")){
                    nodeType=object.getString("type");
                }
                else{
                    nodeType = "String";
                }
                if(object.containsKey("default")){
                    defaultVal = object.getString("default");
                    hasDefault = true;
                }
                else{
                    defaultVal = null;
                }
            } catch (JSONException e) {
                try{
                    nodeType=inputs.getString(loop);
                } catch (JSONException f) {
                    nodeType=null; 
                }
            }
            if (!hasDefault) {
                this.required += 1;
            }
            Map<String, Object> map = new HashMap<String, Object>();
            map.put("type",nodeType);
            map.put("has_default",hasDefault);
            map.put("default",defaultVal);
            try {
                this.inputParams.add(JSONObject.fromObject(map));
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
    }
}
