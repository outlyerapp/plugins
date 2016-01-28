#! /usr/bin/env ruby
# Author: Russell-IO https://github.com/Russell-IO
# either use a command line arguements, or optionally a config file for check identifier
# This means you can deploy a yaml config file to allow you to have one check etc.
# exmaple ./pingdom.rb --execute --account pingdom@you.com --password abc123 --token def456 --config /etc/config.yml
require 'main'
require 'yaml'
require 'httparty'

Main {
  option('execute'){
    argument :optional
    description 'execute the check'
  }
  option('hostname'){
    argument :optional
    description 'Specify The Stack to check'
  }
  option('username'){
    argument :optional
    description 'Specify the Username'
  }
  option('password'){
    argument :optional
    description 'Specify the Password'
  }
  option('authtoken'){
    argument :optional
    description 'Specify the authtoken'
  }
  option('account'){
    argument :optional
    description 'Specify the account'
  }
  option('url'){
    argument :optional
    defaults 'https://api.pingdom.com/api/2.0/checks'
    description 'Optionally override the pingdom endpoint'
  }
  option('config'){
    argument :optional
    description 'Path of Config file'
  }

  def run
      if params['execute'].value == true
        # Capture a HUP signal and act accordingly
        Signal.trap("HUP") { Process.kill("HUP");  Process.wait }

	# Set variables from arguements
	hostname = "#{params['hostname'].value}"
	username = "#{params['username'].value}"
	password = "#{params['password'].value}"
	authtoken = "#{params['authtoken'].value}"
	account = "#{params['account'].value}"
	url = "#{params['url'].value}"

	# update params from config file if specified
	if params['config'].value != "false"
	  config =  YAML.load_file("#{params['config'].value}")
	  hostname = "#{config['hostname']}"
	end

	#Build response headers
	auth =
	  {
	    :username => "#{username}",
	    :password => "#{password}"
	  }
	headers =
	  {
	    "App-Key" => authtoken,
	    "Account-Email" => account
	  }

	# Execute the api request
	response =
	  HTTParty.get(
	    "#{url}?tags=dataloop",
	    :basic_auth => auth,
	    :headers => headers
	  )

	# Select the HTTPS request for the stack in question
	stack = response['checks'].select { |hash| hash['hostname'] == "#{hostname}" }
	https = stack

	# Set the response vars
	status = https.first['status']
	lrtime = https.first['lastresponsetime']

	# Build the nagios response
	case status
	when "up"
	  puts "OK | responsetime=#{lrtime};;;;"
	  exit_status 0
	  exit_success!
	when "down"
	  puts "DOWN | responsetime=#{lrtime};;;;"
	  exit_status 2
	  exit_failure!
	when "unconfirmed_down"
	  puts "UNCONFIRMED | responsetime=#{lrtime};;;;"
	  exit_status 1
	  exit_failure!
	when "paused"
	  puts "PAUSED | responsetime=#{lrtime};;;;"
	  exit_status 1
	  exit_failure!
	else
	  puts "UNKNOWN | responsetime=#{lrtime};;;;"
	  exit_status 3
	  exit_failure!
	end
      else
        puts "--execute hasn't been specified check --help"
      end
  end
}
