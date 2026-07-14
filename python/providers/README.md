# jharness-providers

`jharness-providers` contains optional concrete implementations of the
provider-neutral `jharness.kernel.Model` protocol. Public adapters are imported from
provider namespaces:

```bash
uv add jharness-providers
```

```python
from jharness.providers.anthropic import AnthropicModel
from jharness.providers.deepseek import deepseek_anthropic_profile
from jharness.providers.openai import OpenAIChatCompletionsModel
```

Provider transports, profiles, and codecs do not define runtime semantics.
See the
[provider documentation](https://github.com/Ezio2000/jharness-python/blob/main/docs/model-providers.md)
and
[Python package boundaries](https://github.com/Ezio2000/jharness-python/blob/main/docs/python-package-boundaries.md).
