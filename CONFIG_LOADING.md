# Automatic Configuration Loading

This ACME project includes automatic configuration file loading to simplify setup and usage.

## Overview

The `config_loader.py` module automatically discovers and loads configuration files from standard locations without requiring manual specification each time the application runs.

## Configuration File Formats

Three formats are supported:

- **YAML** (`.yaml`, `.yml`) - Recommended for complex configurations
- **JSON** (`.json`) - Good for structured data
- **.env** - Simple key=value format for environment variables

## Search Paths

Configuration files are searched in the following order:

1. Current directory: `./acme.yaml` or `./acme.json` or `./.env`
2. User home: `~/.acme/config.yaml`, `~/.acme/config.json`, or `~/.acmerc`
3. System-wide: `/etc/acme/config.yaml` or `/etc/acme/config.json`

The **first file found is used**. Later paths are only searched if earlier files don't exist.

## Usage

### Basic Usage

```python
from config_loader import load_config

# Load configuration automatically
config = load_config()

# Access values
rfc_tool = config.get('build.rfc_tool', 'xml2rfc')
```

### Advanced Usage

```python
from config_loader import ConfigLoader, ConfigLoadError

# Create a loader with custom paths
loader = ConfigLoader(
    config_paths=['./my-config.yaml', '/etc/acme/config.json'],
    env_var='ACME_CONFIG'
)

# Load configuration (required=True raises error if not found)
try:
    config = loader.load(required=True)
except ConfigLoadError as e:
    print(f"Configuration error: {e}")

# Access values
value = config.get('some_key', 'default_value')
value = config['some_key']  # Raises KeyError if not found
if 'some_key' in config:
    print(f"Found: {config['some_key']}")
```

## Environment Variable Override

Set the `ACME_CONFIG` environment variable to override default paths:

```bash
# Override config location
export ACME_CONFIG=/path/to/custom/config.yaml
python config_loader.py

# Or in a single command
ACME_CONFIG=/etc/acme/production.yaml python script.py
```

## Creating Configuration Files

### YAML Format

Copy `acme.example.yaml` to a default location and edit:

```bash
cp acme.example.yaml ~/.acme/config.yaml
# Edit configuration
nano ~/.acme/config.yaml
```

### .env Format

Copy `.acmerc.example` and edit:

```bash
cp .acmerc.example ~/.acmerc
# Edit configuration
nano ~/.acmerc
```

### JSON Format

Create `acme.json`:

```json
{
  "build": {
    "rfc_tool": "xml2rfc",
    "output_format": "html"
  },
  "logging": {
    "level": "INFO"
  }
}
```

## Integration Examples

### With Build System

```python
from config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load()

rfc_tool = config.get('build.rfc_tool', 'xml2rfc')
output_format = config.get('build.output_format', 'html')

# Use in build process
os.system(f'{rfc_tool} draft.xml -o output.{output_format}')
```

### With Application Startup

```python
import logging
from config_loader import ConfigLoader, ConfigLoadError

# Load configuration on startup
try:
    loader = ConfigLoader()
    config = loader.load()
except ConfigLoadError as e:
    print(f"Failed to load configuration: {e}")
    sys.exit(1)

# Configure logging from config
log_level = config.get('logging.level', 'INFO')
logging.basicConfig(level=log_level)
```

## Troubleshooting

### Config File Not Found

If no configuration file is found and you're using `load(required=True)`:

```
ConfigLoadError: No configuration file found. Searched:
  ./acme.yaml
  ./acme.json
  ./.env
  ~/.acme/config.yaml
  ~/.acme/config.json
  ~/.acmerc
  /etc/acme/config.yaml
  /etc/acme/config.json
Set ACME_CONFIG environment variable to override.
```

**Solution:** Create a config file in one of the searched locations:

```bash
cp acme.example.yaml ~/.acme/config.yaml
```

### Missing Dependencies

If you see YAML errors:

```
ConfigLoadError: YAML support not available. Install PyYAML: pip install pyyaml
```

**Solution:** Install required dependencies:

```bash
pip install pyyaml
pip install python-dotenv  # Optional, for better .env support
```

### Permission Denied

If you get permission errors when trying to write to `/etc/acme/`:

**Solution:** Use a user-writable location instead:

```bash
mkdir -p ~/.acme
cp acme.example.yaml ~/.acme/config.yaml
```

## Best Practices

1. **Don't commit secrets** - Keep API keys and passwords in local config files, not in git
2. **Use .gitignore** - Add config files to `.gitignore`:
   ```
   acme.yaml
   acme.json
   .acmerc
   .env
   ```

3. **Provide examples** - Keep example files in the repo so users know what to configure

4. **Document all options** - Update `acme.example.yaml` when adding new configuration options

5. **Use environment overrides** - Allow environment variables to override file settings for CI/CD and containers

6. **Validate configuration** - Check for required settings on startup:
   ```python
   config = load_config()
   required_keys = ['build.rfc_tool', 'logging.level']
   for key in required_keys:
       if key not in config:
           raise ConfigError(f"Required config key missing: {key}")
   ```

## Running the Demo

Test the config loader directly:

```bash
# Create a config file
cp acme.example.yaml ./acme.yaml

# Run the demo
python config_loader.py

# Output:
# [INFO] Configuration loaded from: ./acme.yaml
#
# Loaded Configuration (9 keys):
#   build: {...}
#   ...
```

## Related Files

- `config_loader.py` - Main configuration loading module
- `acme.example.yaml` - Example YAML configuration
- `.acmerc.example` - Example .env format configuration
- `rfced/clean-xml-config.py` - Example integration with config loader
