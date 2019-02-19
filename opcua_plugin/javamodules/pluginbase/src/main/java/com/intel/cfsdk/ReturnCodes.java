package com.intel.cfsdk;

public enum ReturnCodes {
    Good(0),
    PLUGIN_ParamError(0x00004000),
    PLUGIN_RpcError(0x00004001);

    private int nCode;
    private ReturnCodes(int _nCode){
        this.nCode=_nCode;
    }

    public int getValue(){
        return this.nCode;
    }
}
