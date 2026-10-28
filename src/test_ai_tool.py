
from apex.ai_tools import compare_f1_drivers

result = compare_f1_drivers.invoke({
    "driver_a": "HAM",
    "driver_b": "VER",
})

print(result)
