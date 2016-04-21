package com.example.lunchapp;

import android.app.ListActivity;
import android.os.Bundle;
import android.widget.ArrayAdapter;

public class CuisineListActivity extends ListActivity {

	public void onCreate(Bundle savedInstanceState) {
	    super.onCreate(savedInstanceState);
	    String[] values = new String[] { "Chinese", "Indian", "Cajun",
	        "French", "Hibachi", "Mongolian", "BBQ", "Mexican"};
	    
	    ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_list_item_1, values);
	    setListAdapter(adapter);
	  }
}
