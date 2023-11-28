#include <AccelStepper.h>
#include <Stepper.h>

//==========================================================================
const int MAX_BEZIER_PROFILE_SIZE = 350; // Set your desired maximum size
// This uses a large amount of the memory on the arduino!!! 
//===========================================================================
//pin assignments for Motor 1
const int dirPin_1 = 38; 
const int stepPin_1 = 40;
const int Sleep_1 = 42;
const int Reset_1 = 44;
const int M2_1 = 46;
const int M1_1 = 48;
const int M0_1 = 50;
const int Enable_1 = 52;
const int LEDPin_1 = 13;


//=============================================================================
//pin assignments for Motor 2
const int dirPin_2 = 22;
const int stepPin_2 = 24;
const int Sleep_2 = 26;
const int Reset_2 = 28;
const int M2_2 = 30;
const int M1_2 = 32;
const int M0_2 = 34;
const int Enable_2 = 36;

const int LEDPin_2 = 13;


#define motorInterfaceType 1


//===========================================================================
// pin assignments for Motor 3 (dimple)

const int dirPin_3 = 53; 
const int stepPin_3 = 51;
const int Sleep_3 = 49;
const int Reset_3 = 47;
const int M2_3 = 45;
const int M1_3 = 43;
const int M0_3 = 41;
const int Enable_3 = 39;

//=============================================================================

int analogPin = A0;
int val = 0;
const int RelayPin = 4;
unsigned long TimeD;
String state;
int k = 0;

int start_pos_1; //start and end positions of motors 1 and 2
int fin_pos_1;
int start_pos_2;
int fin_pos_2;

unsigned long prht_time; //preheat time and time delay
int SPD_1; //speed variables
int SPD_2;
int SPD_3;

int ACC_1; //acceleration variables
int ACC_2;

unsigned short accel_duration = 0;
unsigned short waist_duration = 0; // time at maximum speed during taper
unsigned short decel_duration = 0; // maximum 30'000 milliseconds

int DEC_1; //deceleration variables
int DEC_2;

int TEN_1; //position variables for tension decrease in dimpling
int TEN_2;
long int DIM_P; //number of steps to dimple 

int home1; //home positions to return to 
int home2;
int home3;

int taper_steps;
int depth;

bool fiberBroken = false;

//==========================================================================
// Struct for Point
struct Point {
    float x; // Time in milliseconds
    float y; // Speed in steps per second
};

//=============================================================================
// StepperMotor class
class BezierCurve {
  public:
    void setBezierCurve(Point points[], int size) {
        num_points = size;
        for (int i = 0; i < size; i++) {
            control_points[i] = points[i];
        }
    }

    void calculateAccelProfile() {
        for (int i = 0; i < accelProfileLen; ++i) {
            float t = (float)i / (accelProfileLen - 1);
            accelProfile[i] = calculateBezier(t);;
        }
    }

    void calculateDecelProfile() {
        for (int i = 0; i < decelProfileLen; ++i) {
            float t = (float)i / (decelProfileLen - 1);
            decelProfile[i] = calculateBezier(t);
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

    int getMaxTime() { return getDecelPoint(decelProfileLen-1).x; }

    int getAccelProfileLen() { return accelProfileLen; }

    int getDecelProfileLen() { return decelProfileLen; }
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
        //y = constrain(y, MIN_SPS, MAX_SPS);

        Point result = {x, y};
        return result;
    }


    static constexpr int accelProfileLen = MAX_BEZIER_PROFILE_SIZE/2;
    static constexpr int decelProfileLen = MAX_BEZIER_PROFILE_SIZE/2;
    Point control_points[4]; // Adjust size as needed
    Point accelProfile[accelProfileLen];
    Point decelProfile[decelProfileLen];
    int num_points;
    int bezierProfileSize;
};

// ===========================================================================
struct MotorState {
    int counter;
    unsigned long currentMicros;
    unsigned long initialMicros;
    AccelStepper& stepper;
    BezierCurve& curve;

    MotorState(AccelStepper& stepperRef, BezierCurve& curveRef)
        : stepper(stepperRef), curve(curveRef), counter(0), currentMicros(0) {
        initialMicros = micros();
    }
};

//============================================================================
AccelStepper myStepper_1(motorInterfaceType, stepPin_1, dirPin_1);
AccelStepper myStepper_2(motorInterfaceType, stepPin_2, dirPin_2);
AccelStepper myStepper_3(motorInterfaceType, stepPin_3, dirPin_3);

//===========================================================================
BezierCurve curvemotor1;
BezierCurve curvemotor2;
//===========================================================================
MotorState motorState1(myStepper_1, curvemotor1);
MotorState motorState2(myStepper_2, curvemotor2);

void setup() {
  Serial.begin(9600); //serial initialization

  // Populate bezier curves slow stage
  Point accelPoints1[] = {{0, 80}, {3000,40}, {8000, 20}, {10000, 20}};
  Point decelPoints1[] = {{12000, 20}, {14000, 20}, {16000, 20}, {18000, 40}};
  curvemotor1.setBezierCurve(accelPoints1, 4);
  curvemotor1.calculateAccelProfile();
  curvemotor1.setBezierCurve(decelPoints1, 4);
  curvemotor1.calculateDecelProfile();

  // populate bezier curves fast stage
  Point accelPoints2[] = {{0, 0}, {325,-100}, {10000, 0}, {10000, -700}};
  Point decelPoints2[] = {{12000, -700}, {12000, 0}, {17000, -100}, {18000, 20}};
  curvemotor2.setBezierCurve(accelPoints2, 4);
  curvemotor2.calculateAccelProfile();
  curvemotor2.setBezierCurve(decelPoints2, 4);
  curvemotor2.calculateDecelProfile();

  pinMode(Sleep_1, OUTPUT); //motor 1 pin initialization
  pinMode(Reset_1, OUTPUT);
  pinMode(M2_1, OUTPUT);
  pinMode(M1_1, OUTPUT);
  pinMode(M0_1, OUTPUT);
  pinMode(Enable_1, OUTPUT);

  digitalWrite(Sleep_1, HIGH); //setting resolution, enable
  digitalWrite(Reset_1, HIGH);
  Resolution(1, "HI");
  digitalWrite(Enable_1, LOW);
  pinMode(dirPin_1, OUTPUT);
  pinMode(stepPin_1, OUTPUT);

  pinMode(RelayPin, OUTPUT); //relay outputs
  digitalWrite(RelayPin, LOW);
  pinMode(2, OUTPUT);
  digitalWrite(2, HIGH);
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW);

  myStepper_1.setAcceleration(2000); //steps/s^2
  //---------------------------------------------------------------------------------------
  pinMode(Sleep_2, OUTPUT); //motor 2 pin initialization
  pinMode(Reset_2, OUTPUT);
  pinMode(M2_2, OUTPUT);
  pinMode(M1_2, OUTPUT);
  pinMode(M0_2, OUTPUT);
  pinMode(Enable_2, OUTPUT);

  digitalWrite(Sleep_2, HIGH); //set resolution, enable
  digitalWrite(Reset_2, HIGH);
  Resolution(2, "HI");
  digitalWrite(Enable_2, LOW);
  pinMode(dirPin_2, OUTPUT);
//==========================================================================
//motor 3
 pinMode(Sleep_3, OUTPUT); //motor 3 pin initialization
  pinMode(Reset_3, OUTPUT);
  pinMode(M2_3, OUTPUT);
  pinMode(M1_3, OUTPUT);
  pinMode(M0_3, OUTPUT);
  pinMode(Enable_3, OUTPUT);

  digitalWrite(Sleep_3, HIGH); //set resolution, enable
  digitalWrite(Reset_3, HIGH);
  Resolution(3, "HI");
  digitalWrite(Enable_3, LOW);

  home1 = myStepper_1.currentPosition(); //record home positions
  home2 = myStepper_2.currentPosition();
  home3 = myStepper_3.currentPosition();
  
  myStepper_1.setMaxSpeed(3000); //maximum speeds for each motor
  myStepper_2.setMaxSpeed(3000);
  myStepper_3.setMaxSpeed(3000);
  //------------------------------------------------------------------------------
}


void loop() {

  // delay(2000);
  // moveOneMotorWithBezierCurve(myStepper_2, curvemotor2);
  // delay(2000);
  // taper();
  // delay(10000);

  if (Serial.available() > 0) { 
    state = Serial.readStringUntil('\n'); //get command
    state.trim();
    Serial.println(state);
    if (state.substring(0, 7) == "ENABL_1" ) {
      digitalWrite(Enable_1, LOW);
      Serial.println("Motor 1 enabled");
    }
    //=====================================================================================================================
    //disable motor 1
    else if (state.substring(0, 7) == "DISAB_1" ) {
      digitalWrite(Enable_1, HIGH);
      Serial.println("Motor 1 disabled");
    } 
    //=====================================================================================================================
    //set resolution low for motor1
    else if (state.substring(0, 3) == "RES" ) {
      int num = state.substring(6,7).toInt();
      String com = state.substring(3,5);
      Resolution(num, com);
    } 
    //=====================================================================================================================
    //set speed of motor 1
    else if (state.substring(0, 5) == "SETSP" ) {
      int num = (state.substring(6,7)).toInt(); //speed input
      Speed(num);
    }
    //=====================================================================================================================
    //set acceleration of motor 1
    else if (state.substring(0, 5) == "SETAC" ) {
      int num = (state.substring(6,7)).toInt(); //acceleration input
      Acceleration(num);
    }

    //=====================================================================================================================
    else if (state.substring(0,6) == "ACCDUR") {
      accel_duration = (state.substring(6,12)).toInt();
      Serial.println(accel_duration);
    }

    //=====================================================================================================================
    else if (state.substring(0,6) == "TAPSTP") {
      taper_steps = (state.substring(6,12)).toInt();
      Serial.println(taper_steps);

    }

        //=====================================================================================================================
    //enable motor 2
    else if (state.substring(0, 7) == "ENABL_2" ) {
      digitalWrite(Enable_2, LOW);
      Serial.println("Motor 2 enabled");
    }
    //=====================================================================================================================
    //disable motor 2
    else if (state.substring(0, 7) == "DISAB_2" ) {
      digitalWrite(Enable_2, HIGH);
      Serial.println("Motor 2 disabled");
    } 
    //=====================================================================================================================
    //move motor 2 forward

    //=========================================================================================================
    //recieve preheat data

    else if (state.substring(0,4) == "prht"){
      prht_time = (state.substring(4,12)).toInt();
      Serial.println(prht_time);
    }
    //=====================================================================================================================
    //dimple delay time
    else if (state.substring(0,4) == "TIME"){ 
      TimeD = (state.substring(4,12)).toInt();
    }
    else if(state.substring(0,5) == "DEPTH"){
        int depth = (state.substring(5, 12)).toInt();
    }
    //====================================================================================================================
    //Tension for motor 1 during dimpling
    else if (state.substring(0,4) == "TEN1"){
      TEN_1 = (state.substring(4,12)).toInt();
    }
    //Tension for motor 2 during dimpling
    else if (state.substring(0,4) == "TEN2"){
      TEN_2 = (state.substring(4,12)).toInt();
    }

    //===================================================================================================================
    // Time at maximum tension
    else if(state.substring(0,7) == "WAIST_T"){
      waist_duration = (state.substring(7,12)).toInt();
    }

    //=====================================================================================================================
    //relay on
    else if (state.substring(0,6) == "RLY_ON"){ //toggle relay on
      Rly_on();
    }
    //=====================================================================================================================
    //relay off
    else if (state.substring(0,6) == "RLY_OF"){ //Toggle relay off
      Rly_off();
    }

    if (!fiberBroken){
      if (state.substring(0,6) == "BROKEN") {
        fiber_broken();
      }
      //=====================================================================================================================
      //move motor 1 forward
      else if (state.substring(0, 7) == "MOVRF_1") {
        int STP_1 = (state.substring(7, 12)).toInt(); //how many steps to take
        myStepper_1.setCurrentPosition(0);
        digitalWrite(dirPin_1, LOW);
        delay(1000);
        Serial.println("Done");
        while (myStepper_1.currentPosition() < STP_1) {
          myStepper_1.move(STP_1);
          myStepper_1.run();
        }
      } 
      //=====================================================================================================================
      //move motor 1 backwards
      else if (state.substring(0, 7) == "MOVRB_1" ) {
        int STP_1 = (state.substring(7, 12)).toInt(); //how many steps to move
        myStepper_1.setCurrentPosition(0);
        digitalWrite(dirPin_1, HIGH); // Set direction pin for backwards movement
        Serial.println("Moving motor 1 backward...");

        while (myStepper_1.currentPosition() > -STP_1) {
            myStepper_1.move(-STP_1); // Negative steps for backward movement
            myStepper_1.run();
        }
        Serial.println("Done");
        Serial.println(myStepper_1.currentPosition());
      }

      else if (state.substring(0, 7) == "MOVRF_2" ) {
        int STP_2 = (state.substring(7, 12)).toInt(); //data of how many steps to move
        myStepper_2.setCurrentPosition(0);
        digitalWrite(dirPin_2, LOW); //set direction pin to move forward
        Serial.println("Done");
        while (myStepper_2.currentPosition() < STP_2) { //run stepper
          myStepper_2.move(STP_2);
          myStepper_2.run();
        }
      } 

      //=====================================================================================================================
      //Move motor 2 backwards
      else if (state.substring(0, 7) == "MOVRB_2" ) {
        int STP_2 = (state.substring(7, 12)).toInt(); //data of how many steps to move
        myStepper_2.setCurrentPosition(0);
        digitalWrite(dirPin_2, HIGH); // Set direction pin for backwards movement
        Serial.println("Moving motor 2 backward...");

        while (myStepper_2.currentPosition() > -STP_2) {
            myStepper_2.move(-STP_2); // Negative steps for backward movement
            myStepper_2.run();
        }

        Serial.println("Done");
        Serial.println(myStepper_2.currentPosition());
      }

      //============================================================================================================
      //run motor to taper with linear profile
    else if  (state.substring(0, 6) == "TAPERB"){
        digitalWrite(RelayPin, HIGH);
        delay(0.5); 
        taper();
        digitalWrite(RelayPin, LOW);
        Serial.println("Tapering Complete");
    }

    else if (state.substring(0, 5) == "TAPER"){
        myStepper_2.move(-200000);
        myStepper_1.move(200000);

        digitalWrite(RelayPin, HIGH);
        delay(prht_time); 

        bool stop = false;
        unsigned long startTime = millis();
        start_pos_1 = myStepper_1.currentPosition();
        start_pos_2 = myStepper_2.currentPosition();
        while (myStepper_2.distanceToGo() != 0) {
          myStepper_2.run();
          myStepper_1.run();
          new_string();
          if (millis() - startTime > accel_duration + waist_duration && !stop) {
              Serial.println("Stop");
              stop = true;
              myStepper_1.stop();
              myStepper_2.stop();
          }

        }
        Serial.println("Stopped");
        digitalWrite(RelayPin, LOW);
        Serial.println("Tapering Complete");

        fin_pos_1 = myStepper_1.currentPosition();
        fin_pos_2 = myStepper_2.currentPosition();

      }
      
      //=====================================================================================================================
      //Reset to Home Position
      else if (state.substring(0,4) == "HOME"){ //reset button
        Serial.println("Reseting");
        
        Serial.println(home1); //Positions to return to
        Serial.println(home2);      

        Serial.println(myStepper_1.currentPosition()); //current positions
        Serial.println(myStepper_2.currentPosition());

        Resolution(1, "HA"); //set resolution to be the same
        Resolution(2, "HA");
      
        myStepper_1.moveTo(home1); //move and speed commands
        myStepper_1.setMaxSpeed(2000);

        myStepper_2.moveTo(home2);
        myStepper_2.setMaxSpeed(2000);
    
        while (myStepper_2.distanceToGo()!=0){ //execute run
          myStepper_2.run();
          myStepper_1.run();
          new_string();
        }
        Serial.println(myStepper_2.currentPosition()); 
        Serial.println("Motor 2 home");
      
        Serial.println(myStepper_1.currentPosition());
        Serial.println("motor 1 home");
      }
      //=====================================================================================================================
      //Move the taper to the electrodes

      else if (state.substring(0,5) == "CENTR"){
        float targ_pos_2 = (fin_pos_2+taper_steps/2); //calculate center positions
        float targ_pos_1 = (fin_pos_1-taper_steps/2);

        Resolution(1,"HA"); //set to same resolution
        delay(500);
        Resolution(2,"HA");

        Serial.println(targ_pos_1); //target position
        Serial.println(targ_pos_2);
        
        Serial.println(myStepper_1.currentPosition()); //current position
        Serial.println(myStepper_2.currentPosition());
        
        myStepper_2.setAcceleration(10000); //move, acceleration commands
        myStepper_2.moveTo(targ_pos_2);
        myStepper_2.setMaxSpeed(500);

        myStepper_1.setAcceleration(10000);
        myStepper_1.moveTo(targ_pos_1);
        myStepper_1.setMaxSpeed(500);

        while (myStepper_2.distanceToGo()!=0){ //execute commands
          myStepper_1.runSpeed();
          myStepper_2.runSpeed();
          new_string();
        }    
        Serial.println(myStepper_1.currentPosition()); //finish positions, centered
        Serial.println(myStepper_2.currentPosition());
        Serial.println("Centered");
      }
      

      //=====================================================================================================================
      //dimple using the third motor
      else if(state.substring(0,6) == "DIMPLE"){
        digitalWrite(Enable_1, LOW); //enable all motor
        digitalWrite(Enable_2, LOW);
        digitalWrite(Enable_3, LOW);

        myStepper_3.setAcceleration(1000); //set accelerations
        myStepper_3.setMaxSpeed(3000);
        myStepper_2.setAcceleration(100);
        myStepper_1.setAcceleration(100);

        home3 = myStepper_3.currentPosition(); //set home position

        DIM_P = 86000;

        myStepper_3.moveTo(DIM_P);// set move value

        myStepper_2.setMaxSpeed(SPD_2); // speed for motors 1 and 2
        myStepper_1.setMaxSpeed(SPD_1);
        while(myStepper_3.distanceToGo()!=0){ //execute commands
          myStepper_3.run();
          new_string();
        }

        myStepper_3.setAcceleration(100);
        myStepper_1.move(TEN_1);//Motors 1 and 2 move towards each other to lessen the tension
        myStepper_2.move(TEN_2);
        myStepper_3.moveTo(DIM_P+depth);
        while (myStepper_3.distanceToGo() != 0 || myStepper_1.distanceToGo() != 0 || myStepper_2.distanceToGo() != 0) {
          if (myStepper_3.distanceToGo() != 0) {
            myStepper_3.run();
          }

          if (myStepper_1.distanceToGo() != 0) {
            myStepper_1.run();
          }

          if (myStepper_2.distanceToGo() != 0) {
            myStepper_2.run();
          }

          new_string(); // I assume this is some function you want to run repeatedly during this process?
        }
        
        digitalWrite(RelayPin, HIGH); //electrodes on
        delay(TimeD); //time delay
        digitalWrite(RelayPin, LOW);//electrodes off
        myStepper_3.setAcceleration(1000);

        myStepper_3.moveTo(home3); //move home and  don't retension
        myStepper_2.move(-TEN_2);
        myStepper_1.move(-TEN_1);

        delay(1500);

        while (myStepper_3.distanceToGo()!=0){//execute commands
          myStepper_3.run();
          myStepper_2.run();
          myStepper_1.run();
          new_string();
        }    
        Serial.println("Dimple complete");
      }
      // =============================================================================================================
      // Calibrate Knife position
      else if(state.substring(0,5) == "KNIFD"){
        digitalWrite(Enable_3, LOW);  //enable motor

        myStepper_3.setAcceleration(3000); //set accelerations

        home3 = myStepper_3.currentPosition(); //set home position
        DIM_P = 86000;
        myStepper_3.moveTo(DIM_P);// set move value

        Serial.println(DIM_P);
        Serial.println(myStepper_3.distanceToGo());
        while(myStepper_3.distanceToGo()!=0){ //execute commands
          myStepper_3.run();
          new_string();
        }
        Serial.println("Knife Down");
      }

      else if(state.substring(0,5) == "KNIFU"){
        myStepper_3.moveTo(home3); //move home
        delay(1500);
        while (myStepper_3.distanceToGo()!=0){//execute commands
          myStepper_3.run();
          new_string();
        }   
        Serial.println("Knife Up");
      }

      else if(state.substring(0,5) == "KNDTH"){

        // Calculate the target position by subtracting 100 steps from the current position
        long targetPosition = myStepper_3.currentPosition() + 500;

        // Move motor 3 to the calculated target position
        myStepper_3.moveTo(targetPosition);

        Serial.println("Moving Motor Down 500 Steps...");
        Serial.print("Target Position: ");
        Serial.println(targetPosition);

        // Continue moving motor 3 until it reaches the target position
        while (myStepper_3.distanceToGo() != 0) {
          myStepper_3.run();
          new_string(); // Handle additional commands if received
        }

        Serial.println("Motor Moved Down 1000 Steps");
      }
      else if(state.substring(0,5) == "KFUTH"){

        // Calculate the target position by adding 100 steps from the current position
        long targetPosition = myStepper_3.currentPosition() - 500;

        // Move motor 3 to the calculated target position
        myStepper_3.moveTo(targetPosition);

        Serial.println("Moving Motor Up 500 Steps...");
        Serial.print("Target Position: ");
        Serial.println(targetPosition);

        // Continue moving motor 3 until it reaches the target position
        while (myStepper_3.distanceToGo() != 0) {
          myStepper_3.run();
          new_string(); // Handle additional commands if received
        }

        Serial.println("Motor Moved Down 1000 Steps");
      }

  //=====================================================================================================================
    }
    if (fiberBroken){

      Resolution(1, "HA"); //set resolution to be the same
      Resolution(2, "HA");
      // Move all motors back to their home positions
      myStepper_1.moveTo(home1);
      myStepper_2.moveTo(home2);
      myStepper_3.moveTo(home3);

      Serial.println("Returning to Home Positions...");

      // Continue moving motors until they reach their home positions
      while (myStepper_1.distanceToGo() != 0 || myStepper_2.distanceToGo() != 0 || myStepper_3.distanceToGo() != 0) {
        if (myStepper_1.distanceToGo() != 0) {
          myStepper_1.run();
        }
        if (myStepper_2.distanceToGo() != 0) {
          myStepper_2.run();
        }
        if (myStepper_3.distanceToGo() != 0) {
          myStepper_3.run();
        }
      }
      Serial.println("Returned to Home Positions");
      new_string(); // Handle additional commands if received
    }
  }
}

void Emg_stp(){ //disables both motors and the electrodes

  digitalWrite(RelayPin, LOW);
  digitalWrite(Enable_1, HIGH);
  digitalWrite(Enable_2, HIGH);
  digitalWrite(Enable_3, HIGH);
  Serial.println("Everything is stopped");


}

void Rly_off(){ //turns relay off
  digitalWrite(RelayPin, LOW);
  Serial.println("Relay turned off");
  return;
}

void Rly_on(){ //turns relay on
  digitalWrite(RelayPin, HIGH);
  Serial.println("Relay turned on");
  return;
}

void fiber_broken(){
  Serial.println("Fiber Broken True");
  fiberBroken = true;
}

void new_string(){ //command receives new string and executes command
    if (Serial.available() > 0) {
      String new_string = Serial.readStringUntil('\n'); //new string input while loop is running
      new_string.trim();
      Serial.println(new_string); //calls functions based on input commands
      if (new_string.substring(0,7) == "EMG_STP"){ 
        Emg_stp();
      }
      else if (new_string.substring(0,6) == "BROKEN"){
        fiber_broken();
      }
      else if (new_string.substring(0,6) == "RLY_OF"){
        Rly_off();
      }
      else if (new_string.substring(0,6) == "RLY_ON"){
        Rly_on();
      }
    }
    
}

void Resolution(int num, String res){ //resolution (step size) of all motors
  const int PinArray[4][3] = {{0,0,0},{M0_1, M1_1, M2_1},{M0_2, M1_2, M2_2},{M0_3, M1_3, M2_3}};
  const bool ComArray[3][3] = {{HIGH, HIGH, HIGH}, {LOW, LOW, LOW}, {LOW, LOW, HIGH}};
  int  res_val;
  int x;

  if (res == "HI"){
    res_val = 0;
  }
  else if (res == "LO"){
    res_val = 1;
  }
  else if (res == "HA"){
    res_val = 2;
  }
  for(x =0;x < 3;x++){
    digitalWrite(PinArray[num][x], ComArray[res_val][x]);
  }
  return;
  
}

void Speed(int num){ //speed commands
  Serial.println(num);
  if (num == 1){
    SPD_1 = (state.substring(7,12).toInt());
    myStepper_1.setSpeed(SPD_1);
  }
  else if (num == 2){
    SPD_2 = (state.substring(7,12).toInt());
    //myStepper_2.setMaxSpeed(SPD_2);
    myStepper_2.setSpeed(SPD_2);
  }
  else if (num == 3){
    SPD_3 = (state.substring(7, 12)).toInt();

    myStepper_3.setSpeed(SPD_3);
  }    
}

void Acceleration(int num){ //set acceleration of motors 1 and 2
  if (num == 1){
    ACC_1 = (state.substring(7,12).toInt());
    myStepper_1.setAcceleration(ACC_1);

  }
  else if (num == 2){
    ACC_2 = (state.substring(7,12).toInt());
    myStepper_2.setAcceleration(ACC_2);
  }
}

void taper(){
  // turn on electrodes with preheat 
  Serial.println("A: TAPERING");
  unsigned long startMillis = millis();
  float runTime = millis()-startMillis;
  int motor1RunTime = curvemotor1.getMaxTime();
  int motor2RunTime = curvemotor2.getMaxTime();
  while (runTime < motor1RunTime ||  runTime < motor2RunTime){
    if (runTime < motor1RunTime){
         moveMotorBezier(motorState1);
    }
    if (runTime < motor2RunTime){
        moveMotorBezier(motorState2);
    }
  runTime = millis()-startMillis;
  new_string();
  }
}


void moveMotorBezier(MotorState& motorState) {
    unsigned long elapsedTimeForPoint;

    motorState.stepper.runSpeed();
    motorState.currentMicros = micros(); // Update current time

    int accelProfileLen = motorState.curve.getAccelProfileLen();
    int decelProfileLen = motorState.curve.getDecelProfileLen();

    if (motorState.counter < accelProfileLen + decelProfileLen) {
        if (motorState.counter < accelProfileLen) {
            elapsedTimeForPoint = motorState.curve.getAccelPoint(motorState.counter).x * 1000; // Convert to microseconds
        } else {
            elapsedTimeForPoint = motorState.curve.getDecelPoint(motorState.counter - accelProfileLen).x * 1000;
        }

        if (motorState.currentMicros - motorState.initialMicros >= elapsedTimeForPoint) {
            motorState.counter++; // Move to the next point
            if (motorState.counter < accelProfileLen) {
                motorState.stepper.setSpeed(motorState.curve.getAccelPoint(motorState.counter).y);
            } else {
                motorState.stepper.setSpeed(motorState.curve.getDecelPoint(motorState.counter - accelProfileLen).y);
            }
        }
    } else {
        motorState.stepper.setSpeed(0); // Stop the motor if the end of the curve is reached
    }
}



void moveOneMotorWithBezierCurve(AccelStepper& stepper, BezierCurve& curve) {
    unsigned long initialMicros = micros();
    int counter = 0;
    int accelProfileLen = curve.getAccelProfileLen(); // Assuming you have a method to get this length
    int decelProfileLen = curve.getDecelProfileLen(); // Assuming you have a method to get this length
    unsigned long currentMicros, elapsedTimeForPoint;

    stepper.setSpeed(curve.getAccelPoint(counter).y); // Set initial speed

    while (counter < accelProfileLen + 0.6*decelProfileLen) {
        stepper.runSpeed();
        currentMicros = micros(); // Update current time

        if (counter < accelProfileLen) {
            elapsedTimeForPoint = curve.getAccelPoint(counter).x * 1000; // Convert to microseconds
        } else {
            elapsedTimeForPoint = curve.getDecelPoint(counter - accelProfileLen).x * 1000;
        }

        if (currentMicros - initialMicros >= elapsedTimeForPoint) {
            counter++; // Move to the next point
            if (counter < accelProfileLen) {
                stepper.setSpeed(curve.getAccelPoint(counter).y);
                Serial.println(stepper.speed());
            } else {
                stepper.setSpeed(curve.getDecelPoint(counter - accelProfileLen).y);
                Serial.println(stepper.speed());
            }
        }
    }

    stepper.setSpeed(0); // Stop the motor at the end
}


