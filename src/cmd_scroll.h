#pragma once
#include <stdbool.h>

/* cosmos_adjust_speed - adjusts session pointer/scroll gain, clamped to 25–300%. */
void cosmos_adjust_speed(bool scroll, int delta);
