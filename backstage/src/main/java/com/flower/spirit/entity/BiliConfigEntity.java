package com.flower.spirit.entity;

import java.io.Serializable;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.TableGenerator;

@Entity
@Table(name = "biz_bili_config")
public class BiliConfigEntity implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = 3010593573446198051L;
	
	@Id
	@GeneratedValue(strategy = GenerationType.TABLE,generator="biz_bili_config")
	@TableGenerator(name = "biz_bili_config", allocationSize = 1, table = "seq_common", pkColumnName = "seq_id", valueColumnName = "seq_count")
    private Integer id;
	
	private String bilicookies;
	
	private String bigmember;
	
	private String bitstream;
	
	private String refreshtoken;
	
	private String oddmm;
	
	private String collectdmm;
	
	private String cdnsort;  //是否启用cdn 排序

	public Integer getId() {
		return id;
	}

	public void setId(Integer id) {
		this.id = id;
	}

	public String getBilicookies() {
		return bilicookies;
	}

	public void setBilicookies(String bilicookies) {
		this.bilicookies = bilicookies;
	}

	public String getBigmember() {
		return bigmember;
	}

	public void setBigmember(String bigmember) {
		this.bigmember = bigmember;
	}

	public String getBitstream() {
		return bitstream;
	}

	public void setBitstream(String bitstream) {
		this.bitstream = bitstream;
	}

	public String getRefreshtoken() {
		return refreshtoken;
	}

	public void setRefreshtoken(String refreshtoken) {
		this.refreshtoken = refreshtoken;
	}

	public String getOddmm() {
		return oddmm;
	}

	public void setOddmm(String oddmm) {
		this.oddmm = oddmm;
	}

	public String getCollectdmm() {
		return collectdmm;
	}

	public void setCollectdmm(String collectdmm) {
		this.collectdmm = collectdmm;
	}

	public String getCdnsort() {
		return cdnsort;
	}

	public void setCdnsort(String cdnsort) {
		this.cdnsort = cdnsort;
	}
	
	
	
	

}
