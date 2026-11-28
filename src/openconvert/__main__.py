"""``python -m openconvert`` 的入口，与 ``openconvert`` 脚本等价。"""

import sys

from .cli import main

sys.exit(main())
