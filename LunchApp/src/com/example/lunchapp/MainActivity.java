package com.example.lunchapp;

import android.annotation.SuppressLint;
import android.content.Intent;
import android.os.Bundle;
import android.support.v7.app.ActionBarActivity;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;

@SuppressLint("NewApi")
public class MainActivity extends ActionBarActivity {
	
	
	
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		
		Button loginButton = (Button) findViewById(R.id.loginButton);
		Button signUpButton = (Button) findViewById(R.id.signUpButton);
		
		loginButton.setOnClickListener(new View.OnClickListener(){
			public void onClick(View v){
				//Boolean check = authenticate(email, password);
				//if(check)
				
				Intent signUpIntent = new Intent(MainActivity.this, PlanActivity.class);
				
				//signUpIntent.putExtra("email", email)
				
				MainActivity.this.startActivity(signUpIntent);
			}
			
		});
		
		signUpButton.setOnClickListener(new View.OnClickListener(){
			public void onClick(View v){
				Intent signUpIntent = new Intent(MainActivity.this, NewProfileActivity.class);
				//signUpIntent.putExtra("key", )
				MainActivity.this.startActivity(signUpIntent);
			}
			
		});
	}

	@Override
	public boolean onCreateOptionsMenu(Menu menu) {
		// Inflate the menu; this adds items to the action bar if it is present.
		getMenuInflater().inflate(R.menu.main, menu);
		return true;
	}

	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
		// Handle action bar item clicks here. The action bar will
		// automatically handle clicks on the Home/Up button, so long
		// as you specify a parent activity in AndroidManifest.xml.
		int id = item.getItemId();
		if (id == R.id.action_settings) {
			return true;
		}
		return super.onOptionsItemSelected(item);
	}
	
	//Called when log in button is pressed
	public boolean authenticateUser(String email, String password){
		return true;
	}
	
	
	
	
	
}
