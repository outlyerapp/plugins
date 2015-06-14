#! /usr/bin/env ruby
require 'main'
require 'yaml'
require 'httparty'

# Deps:
# ruby1.9.3 or later
# gem main
# gem httparty
# Useage:
# Explained with --help
# Example:
# ./newrelicstatus.rb --execute --authtoken 'YOUR_API-KEY' --app 'NEW RELIC GUI APP NAME'

Main {
  option('execute'){
    argument :optional
    description 'execute the check'
  }
  option('app'){
    argument :optional
    description 'Specify The Application Human Name to check'
  }
  option('authtoken'){
    argument :optional
    description 'Specify the authtoken'
  }
  option('url'){
    argument :optional
    defaults 'https://api.newrelic.com/v2/applications.json'
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
	app = "#{params['app'].value}"
	authtoken = "#{params['authtoken'].value}"
	url = "#{params['url'].value}"

	# update params from config file if specified
	if params['config'].value != "false"
	  config =  YAML.load_file("#{params['config'].value}")
	  app = config['newrelic_application']
	end

	#Build response headers
	headers =
	  {
	    "X-Api-Key" => authtoken
	  }

	# Execute the api request
	response =
	  HTTParty.get(
	    "#{url}",
	    :headers => headers
	  )

	# Select the HTTPS request for the stack in question
	stack = response['applications'].select { |hash| hash['name'] == "#{app}" }

	# Set the response vars
	status = stack.first['health_status']
	appdex = stack.first['application_summary']['apdex_score']
	lrtime = stack.first['application_summary']['response_time']
	throughput = stack.first['application_summary']['throughput']
	errorrate = stack.first['application_summary']['error_rate']

	# Build the nagios response
	case status
	when "green"
	  puts "OK | appdex=#{appdex} errorrate=#{errorrate} responsetime=#{lrtime} throughput=#{throughput};;;;"
	  exit_status 0
	  exit_success!
	when "yellow"
	  puts "WARNING | appdex=#{appdex} errorrate=#{errorrate} responsetime=#{lrtime} throughput=#{throughput};;;;"
	  exit_status 1
	  exit_failure!
	when "red"
	  puts "CRITICAL | appdex=#{appdex} errorrate=#{errorrate} responsetimr=#{lrtime} throughput=#{throughput};;;;"
	  exit_status 2
	  exit_failure!
	else
	  puts "UNKNOWN | appdex=#{appdex} errorrate=#{errorrate} responsetime=#{lrtime} throughput=#{throughput};;;;"
	  exit_status 3
	  exit_failure!
	end
      else
        puts "--execute hasn't been specified check --help"
      end
  end
}

