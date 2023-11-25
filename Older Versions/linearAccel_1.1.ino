#include <Stepper.h>

const int stepsPerRevolution = 2048;
const int limitRPM = 15;
const float convertSPMStoRPM = 60000.0 / stepsPerRevolution;

int StepsRequired; 
Stepper steppermotor(stepsPerRevolution, 8, 10, 9, 11);

void setup() {
  Serial.begin(9600);
}

void loop() {
  StepsRequired = stepsPerRevolution;
  linearMove(StepsRequired, 200, 200, 15);
  delay(1000);

  StepsRequired = -stepsPerRevolution;
  linearMove(StepsRequired, 200, 200, 10);
  delay(2000);

  StepsRequired = stepsPerRevolution;
  constantMove(StepsRequired, 4000);
  delay(1000);

  StepsRequired = -stepsPerRevolution;
  constantMove(StepsRequired, 6000);
  delay(2000);
}

void constantMove(int steps, unsigned long duration) {
  Serial.println("Starting constantMove function");
  int direction = (steps >= 0) ? 1 : -1;
  steps = abs(steps);

  float rpm = convertSPMStoRPM * steps / duration;
  rpm = constrain(rpm, 1, limitRPM);

  Serial.println(rpm);
  steppermotor.setSpeed(rpm);
  for (int i = 0; i < steps; i++) {
    steppermotor.step(direction);
  }
    Serial.println("constantMove function complete");
}

void linearMove(int steps, float acceleration, float deceleration, float maxRPM) {
  Serial.println("Starting linearMove function");
  int direction = (steps >= 0) ? 1 : -1;
  steps = abs(steps);

  float maxStepsPerSecond = maxRPM * stepsPerRevolution / 60.0;

  float timeToMaxSpeedAccel = maxStepsPerSecond / acceleration;
  float timeToMaxSpeedDecel = maxStepsPerSecond / deceleration;

  int stepsDuringAccel = 0.5 * acceleration * pow(timeToMaxSpeedAccel, 2);
  int stepsDuringDecel = 0.5 * deceleration * pow(timeToMaxSpeedDecel, 2);

  if (stepsDuringAccel + stepsDuringDecel > steps) {
    float totalAccelDecelRatio = (float)stepsDuringAccel / (stepsDuringAccel + stepsDuringDecel);
    stepsDuringAccel = steps * totalAccelDecelRatio;
    stepsDuringDecel = steps - stepsDuringAccel;
  }

  int constantSpeedSteps = steps - stepsDuringAccel - stepsDuringDecel;

  for (int i = 0; i < stepsDuringAccel; i++) {
    float currentStep = i + 1;
    float rpm = sqrt(2 * acceleration * currentStep) * (60.0 / stepsPerRevolution);
    rpm = constrain(rpm, 1, limitRPM);
    steppermotor.setSpeed(rpm);
    steppermotor.step(direction);
  }

  maxRPM = constrain(maxRPM, 1, limitRPM);
  steppermotor.setSpeed(maxRPM);
  for (int i = 0; i < constantSpeedSteps; i++) {
    steppermotor.step(direction);
  }

  for (int i = 0; i < stepsDuringDecel; i++) {
    float remainingSteps = stepsDuringDecel - i;
    float rpm = sqrt(2 * deceleration * remainingSteps) * (60.0 / stepsPerRevolution);
    rpm = constrain(rpm, 1, limitRPM);
    steppermotor.setSpeed(rpm);
    steppermotor.step(direction);
  }

  Serial.println("linearMove function complete");
}
