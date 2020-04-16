# nginx-config-generator

This repository hosts utiltiy to generate a valid Nginx Configuration from the specified input params

### Project Description
The project aims to create a valid Nginx configuration from a generalized yaml template provided as input.

#### Project Structure
The project is divided into the following folders , files 

1. `nginx` :- This folder hosts the backing library file which generates the valid Nginx Configuration .
2. `requirements.txt` :- Standard pythonic way to store the dependencies used in the project.
3. `resources` :- This folder hosts a sample input yaml for the project , and this is the default directory where generated output nginx configs are stored if ouput file path is not specified.
4. `resouces/sample_input.yaml` :-  Sample yaml input file for reference.
5. `resources/sample_generated_nginx.conf` :- Sample Nginx configuration that would be generated for sample input.yaml file. 
6. `nginx_config_generator.py` :- Driver script which builds configuration for Nginx.   

#### Usage

Running the script is quite easy , make sure the pre-requisite dependencies are installed ( as listed in requirements.txt)

`pip3 install requirementts.txt`


Run the script with the following command line params

`nginx_config_generator.py --input <input_yaml_file> --output <output_config_file_path>`


For getting help on the script and params, run the driver script with `--help` argument

```bash
nginx_config_generator.py --help

usage: nginx_config_generator.py [-h] --input INPUT [--output OUTPUT]

Script to generate Nginx Configuration

optional arguments:
  -h, --help       show this help message and exit
  --input INPUT    Location of the input.yaml file to process
  --output OUTPUT  Location where the output nginx donfig would be dumped
                   (this includes the output file name as well
```

#### Few points to note 
1. --input argument is mandatory to be provided for the script to run.
2. --output argument is optional, if not specified the generated Nginx configuration would be created under resources folder.
3. Subsequent run of the script would over-ride the already generated Nginx configuration if the explicity default path is not provided.
