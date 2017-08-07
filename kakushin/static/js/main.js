console.log("HI");


$(document).ready(function(){
	
	var role;
	user={};
	user_login={};

	$(".volunteer_login").click(function(){
		role=0;
		user_login['role']=role;
		// console.log(role);
	});
	$(".ngo_login").click(function(){
		role=1;
		user_login['role']=role;
		// console.log(role);
	});
	$(".donor_login").click(function(){
		role=2;
		user_login['role']=role;
		// console.log(role);
	});

	$(".volunteer_register").click(function(){
		role=0;
		user['role']=role;
		// console.log(role);
	});
	$(".ngo_register").click(function(){
		role=1;
		user['role']=role;
		// console.log(role);
	});
	$(".donor_register").click(function(){
		role=2;
		user['role']=role;
		// console.log(role);
	});


	

	$(".vol_submit").click(function(){
		role=user['role'];
		user={}
		volunteer_reg();
		user['role']=role;
		register_AJAX(user);
		console.log(user);
	})

	$(".ngo_submit").click(function(){
		role=user['role'];
		user={}
		ngo_reg();
		user['role']=role;
		register_AJAX(user)
		console.log(user);
	})

	$(".donor_submit").click(function(){
		role=user['role'];
		user={}
		donor_reg();
		user['role']=role;
		register_AJAX(user);
		console.log(user);
	})

	$(".user_submit").click(function(){
		login_user();
		login_AJAX(user_login);
	})




	

})




function volunteer_reg(){
		vol_name=$("#vol_name").val();
		vol_age=$("#vol_age").val();
		vol_email=$("#vol_email").val();
		vol_password=$("#vol_password").val();
		vol_campus=$("#vol_campus").val();
		vol_city=$("#vol_city").val();
		vol_username=$("#vol_username").val();

		user["name"]=vol_name;
		user["age"]=vol_age;
		user["emailid"]=vol_email;
		user["pass"]=vol_password;
		user["campus"]=vol_campus;
		user["city"]=vol_city;
		user["username"]=vol_username;
		user['primary']=0;
		user['secondary']=0;
		user['chapter']="";

		

}


function ngo_reg(){
		ngo_name=$("#ngo_name").val();
		ngo_age=$("#ngo_age").val();
		ngo_email=$("#ngo_email").val();
		ngo_password=$("#ngo_password").val();
		ngo_state=$("#ngo_state").val();
		ngo_registeration=$("#ngo_registeration").val();
		ngo_city=$("#ngo_city").val();
		ngo_username=$("#ngo_username").val();


		user["name"]=ngo_name;
		user["age"]=ngo_age;
		user["emailid"]=ngo_email;
		user["pass"]=ngo_password;
		user["state"]=ngo_state;
		user["registeration"]=ngo_registeration;
		user["city"]=ngo_city;
		user["username"]=ngo_username;

		
}

function donor_reg(){

		donor_name=$("#donor_name").val();
		donor_email=$("#donor_email").val();
		donor_password=$("#donor_password").val();
		donor_username=$("#donor_username").val();
		donor_pancard=$("#donor_pancard").val();

		user["name"]=donor_name;
		user["emailid"]=donor_email;
		user["pass"]=donor_password;
		user["username"]=donor_username;
		user["pancard"]=donor_pancard;


}


function login_user(){
	    user_username=$("#user_username").val();
	    user_pass=$("#user_pass").val();

	    user_login['username']=user_username;
	    user_login['password']=user_pass;
}


function register_AJAX(){

	$.ajax({
			url:"/register",
			type: "POST",
			data: JSON.stringify(user,null, '\t'),
			contentType: 'application/json; charset=UTF-8',
			success: function(message)
			{
				console.log(message);
				console.log(message.location);
				if(parseInt(message.role)==0){
					window.location.href=message.location;
				}
				
			}});
		
}



function login_AJAX(){

	$.ajax({
			url:"/login",
			type: "POST",
			data: JSON.stringify(user_login,null, '\t'),
			contentType: 'application/json; charset=UTF-8',
			success: function(message)
			{
				console.log(message);
				
				
			}});
}
