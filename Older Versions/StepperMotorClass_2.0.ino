#include <Stepper.h>

// Constants for stepper motor
const int STEPS_PER_REVOLUTION = 2048;
const float MAX_RPM = 15;
const int MAX_SPS = MAX_RPM * STEPS_PER_REVOLUTION / 60; // steps per second
const float MIN_RPM = 0.5;
const int MIN_SPS = MIN_RPM * STEPS_PER_REVOLUTION / 60; // steps per second
const int MAX_BEZIER_PROFILE_SIZE = 80; // Set your desired maximum size
const int MIN_MICRO_DELAY = (1/MAX_SPS)*1000000;  // microseconds
const int MAX_MICRO_DELAY = (1/MIN_SPS)*1000000; // microseconds


String state; // commands sent to arduino using serial port

//
const int FIBER_DEPTH = 1000;
int dimple_depth = 20;

// Struct for Point
struct Point {
    float x; // Time in milliseconds
    float y; // Speed in steps per second
};

// StepperMotor class
class StepperMotor {
  public:

    StepperMotor(int stepsPerRevolution, int pin1, int pin2, int pin3, int pin4)
        : stepper(stepsPerRevolution, pin1, pin2, pin3, pin4), 
          stepsTaken(0), previousStepMicros(0), num_points(0) {}

    void setBezierCurve(Point points[], int size) {
        num_points = size;
        for (int i = 0; i < size; i++) {
            control_points[i] = points[i];
        }
    }

    void calculateAccelProfile() {
        for (int i = 0; i < accelProfileLen; ++i) {
            float t = (float)i / (accelProfileLen - 1);
            accelProfile[i] = calculateBezier(t);
            // Print the x and y values separated by a comma
            //Serial.print(accelProfile[i].x);
            //Serial.print(", ");
            //Serial.println(accelProfile[i].y);
        }
    }

    void calculateDecelProfile() {
        for (int i = 0; i < decelProfileLen; ++i) {
            float t = (float)i / (decelProfileLen - 1);
            decelProfile[i] = calculateBezier(t);
            // Print the x and y values separated by a comma
            //Serial.print(decelProfile[i].x);
            //Serial.print(", ");
            //Serial.println(decelProfile[i].y);
        }
    }

    Point getAccelPoint(int index) {
        if (index >= 0 && index < MAX_BEZIER_PROFILE_SIZE) {
            return accelProfile[index];
        }
        return {0, 0}; // Return a default point if index is out of range
    }

    Point getDecelPoint(int index) {
        if (index >= 0 && index < MAX_BEZIER_PROFILE_SIZE) {
            return decelProfile[index];
        }
        return {0, 0}; // Return a default point if index is out of range
    }

    int getStepsTaken() const { return stepsTaken; }

    int getMaxTime() {return getDecelPoint(decelProfileLen-1).x; }

    void update() {
        unsigned long currentMicros = micros();
        if (currentMicros - previousStepMicros >= delayMicros) {
            stepMotor(direction);
            previousStepMicros = currentMicros;
        }
    }

    void setDirection(int direct){
      direction = direct;
    }

    void startMovement(int direc) {
        initialMicros = micros();
        counter = 0;
        direction = direc;
    }

    void moveMotorBezier() {
        unsigned long currentMicros = micros();
        if (counter < accelProfileLen) {  // Ensuring counter doesn't exceed the size of the Bezier profile
            unsigned long elapsedTimeForPoint = getAccelPoint(counter).x * 1000; // Convert to microseconds
            if (currentMicros - initialMicros >= elapsedTimeForPoint) {

                unsigned long newDelayMicros = (unsigned long)((1.0 / getAccelPoint(counter).y) * 1000000);
                setDelayMicros(newDelayMicros);
                counter++; // Move to the next point
            }
        }
        else if (counter < accelProfileLen + decelProfileLen) {  // Ensuring counter doesn't exceed the size of the Bezier profile
            unsigned long elapsedTimeForPoint = getDecelPoint(counter-accelProfileLen).x * 1000; // Convert to microseconds
            if (currentMicros - initialMicros >= elapsedTimeForPoint) {

                unsigned long newDelayMicros = (unsigned long)((1.0 / getDecelPoint(counter-accelProfileLen).y) * 1000000);
                setDelayMicros(newDelayMicros);
                counter++; // Move to the next point
            }
        }
        update();
    }
    
    void setDelayMicros(unsigned long newDelay) {
      delayMicros = newDelay;
    }

    void stepMotor(int steps) {
        stepper.step(steps);
        stepsTaken += steps;
    }

  private:
    long factorial(int n) {
        if (n < 0) return 0; // Factorial is not defined for negative numbers
        long result = 1;
        for (int i = 2; i <= n; ++i) {
            result *= i;
        }
        return result;
    }

    long combination(int n, int k) {
        if (n < 0 || k < 0 || k > n) return 0; // Ensure valid inputs
        // Since combination(n, k) == combination(n, n-k)
        if (k > n / 2) k = n - k; // Take advantage of symmetry

        long result = 1;
        for (int i = 1; i <= k; ++i) {
            result *= n - (k - i);
            result /= i;
        }
        return result;
    }

    Point calculateBezier(float t) {
        float x = 0;
        float y = 0;
        int n = num_points - 1;

        for (int i = 0; i <= n; i++) {
            // Bernstein basis
            float B = pow(1 - t, n - i) * pow(t, i) * combination(n, i);
            x += control_points[i].x * B;
            y += control_points[i].y * B;
        }

        // Constrain y to be within the SPS range
        y = constrain(y, MIN_SPS, MAX_SPS);

        Point result = {x, y};
        return result;
    }


    int counter;
    unsigned long initialMicros;
    int accelProfileLen = MAX_BEZIER_PROFILE_SIZE/2;
    int decelProfileLen = MAX_BEZIER_PROFILE_SIZE/2;
    Stepper stepper;
    Point control_points[4]; // Adjust size as needed
    Point accelProfile[MAX_BEZIER_PROFILE_SIZE/2]; // Adjust size based on the number of points needed
    Point decelProfile[MAX_BEZIER_PROFILE_SIZE/2]; // Adjust size based on the number of points needed
    int direction;
    int num_points;
    int bezierProfileSize;
    unsigned long delayMicros = 30000; // 30 milliseconds in microseconds
    int stepsTaken;
    unsigned long previousStepMicros;
};

// Global StepperMotor instance
StepperMotor steppermotor1(STEPS_PER_REVOLUTION, 2, 4, 3, 5);
//StepperMotor steppermotor2(STEPS_PER_REVOLUTION, 6, 8, 7, 9);
StepperMotor steppermotor2(STEPS_PER_REVOLUTION, 10, 12, 11, 13);
//StepperMotor steppermotor2(STEPS_PER_REVOLUTION, 4, 6, 5, 7);
//StepperMotor steppermotor3(STEPS_PER_REVOLUTION, 0, 2, 1, 3))

void setup() {
  Serial.begin(9600); //serial initialization


    Point accelPoints1[] = {{0, 0}, {5000,0}, {5000, 512}, {10000, 512}};
    Point decelPoints1[] = {{10000, 512}, {15000,512}, {15000, 0}, {20000, 0}};
    steppermotor1.setBezierCurve(accelPoints1, 4);
    steppermotor1.calculateAccelProfile();
    steppermotor1.setBezierCurve(decelPoints1, 4);
    steppermotor1.calculateDecelProfile();


    // Example control points
    Point accelPoints2[] = {{0, 0}, {1000,0}, {2000, 512}, {3000, 512}};
    Point decelPoints2[] = {{4000, 512}, {5000,512}, {6000, 0}, {7000, 0}};
    steppermotor2.setBezierCurve(accelPoints2, 4);
    steppermotor2.calculateAccelProfile();
    steppermotor2.setBezierCurve(decelPoints2, 4);
    steppermotor2.calculateDecelProfile();


}

void loop() {
  //Serial.println("WHY THIS NEEDED");
  //dimple();
  delay(2000);
  taper();
  delay(2000);
  center();
  delay(2000);
  reset();
  delay(2000);
}


void new_string(){ //command receives new string and executes command
    if (Serial.available() > 0) {
      String new_string = Serial.readStringUntil('\n'); //new string input while loop is running
      new_string.trim();
      }
}

void taper(){
  // turn on electrodes with preheat 
        Serial.println("A: TAPERING");
        steppermotor1.startMovement(1); // Initialize initialMicros for the motor
        steppermotor2.startMovement(-1); // Initialize initialMicros for the motor
        unsigned long startMillis = millis();
        float runTime = millis()-startMillis;
        while (runTime < steppermotor1.getMaxTime() ||  runTime < steppermotor2.getMaxTime()){
            if (runTime < steppermotor1.getMaxTime()){
                steppermotor1.moveMotorBezier();
            }
            if (runTime < steppermotor2.getMaxTime()){
                steppermotor2.moveMotorBezier();
            }
            runTime = millis()-startMillis;
            new_string();
        }
}

void reset(){
    Serial.println("A: RESETTING");
    steppermotor1.setDelayMicros(2000);
    steppermotor2.setDelayMicros(2000);
    if (steppermotor1.getStepsTaken() > 0){
        steppermotor1.setDirection(-1);
    }
    else {
      steppermotor1.setDirection(1);
    }
    if (steppermotor2.getStepsTaken() > 0){
      steppermotor2.setDirection(-1);
    }
    else {
      steppermotor2.setDirection(1);
    }
    while (steppermotor1.getStepsTaken()!= 0 || steppermotor2.getStepsTaken()!= 0 ){
      if (steppermotor1.getStepsTaken()!= 0){
        steppermotor1.update();
      }
      if (steppermotor2.getStepsTaken()!= 0){
        steppermotor2.update();
      }
    }
}

void center(){
    Serial.println("A: CENTERING");
    steppermotor1.setDelayMicros(6000);
    steppermotor2.setDelayMicros(6000);
    if (steppermotor1.getStepsTaken() > 0){
        steppermotor1.setDirection(-1);
    }
    else {
      steppermotor1.setDirection(1);
    }
    if (steppermotor2.getStepsTaken() > 0){
      steppermotor2.setDirection(-1);
    }
    else {
      steppermotor2.setDirection(1);
    }
    int centerPosition1 = steppermotor1.getStepsTaken()/2;
    int centerPosition2 = steppermotor2.getStepsTaken()/2;
    while (steppermotor1.getStepsTaken()!= centerPosition1 || steppermotor2.getStepsTaken()!= centerPosition2 ){
      if (steppermotor1.getStepsTaken()!= centerPosition1){
        steppermotor1.update();
      }
      if (steppermotor2.getStepsTaken()!= centerPosition2){
        steppermotor2.update();
      }
    }
}

void dimple() {
  Serial.println("A: DIMPLING");
  steppermotor2.startMovement(1);
  steppermotor2.setDelayMicros(2000);
  while (steppermotor2.getStepsTaken() != FIBER_DEPTH){
    steppermotor2.update();
  }
  steppermotor2.setDelayMicros(60000);
  // let out tension and turn on electrodes
  while (steppermotor2.getStepsTaken() != FIBER_DEPTH+dimple_depth){
    steppermotor2.update();
  }
  //steppermotor2.setDirection(-1);
  steppermotor2.setDelayMicros(2000);
    while (steppermotor2.getStepsTaken() != 0){
    steppermotor2.update();
  }


}
