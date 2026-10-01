import sys
from types import ModuleType


# Mock uvicorn supervisors to completely avoid touching multiprocessing
class DummySupervisor:
    pass


sup_mod = ModuleType("uvicorn.supervisors")
sup_mod.ChangeReload = DummySupervisor
sup_mod.Multiprocess = DummySupervisor
sys.modules["uvicorn.supervisors"] = sup_mod
sys.modules["uvicorn.supervisors.basereload"] = sup_mod
sys.modules["uvicorn.supervisors.multiprocess"] = sup_mod

import uvicorn  # noqa: E402 - must follow the sys.modules patch above

if __name__ == "__main__":
    uvicorn.run(
        "scai.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
