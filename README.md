# KUKA-powerbank-assembly-safety-AI
![Robodk rdk](RoboDk.png)
# Real-time Human Detection and Robot Safety System with RoboDK Integration

This system integrates a KUKA robot with a real-time human detection system to ensure safe and efficient operation in a shared workspace. By using a camera, OpenCV, and YOLOv8s-seg for human segmentation, the system monitors a predefined "danger zone" around the robot. If a human is detected within this zone, the robot immediately stops its tasks and resumes only when the area is clear. RoboDK is used for offline programming and simulation, generating motion commands for the KUKA robot.

## How It Works

1.  **Camera Setup (Real-time Video Feed)**
    A camera continuously captures the workspace, providing a live video feed for real-time analysis of robot and human movements.

2.  **Human Segmentation (OpenCV + YOLOv8s-seg)**
    The live video feed is processed using OpenCV and the YOLOv8s-seg model. This model detects and segments humans in the workspace, distinguishing them from other objects and the background.

3.  **Human Detected in Danger Zone?**
    The system analyzes the segmented human data to determine if any detected individuals are within a predefined safety area around the robot (the "danger zone").

    * **If a human is detected in the danger zone:**
        * The robot is immediately stopped.
        * A warning message is triggered to alert the operator.
    * **If no human is detected in the danger zone:**
        * The robot resumes its programmed task.

4.  **Robot Assembly Program (Pick and Place Tasks)**
    When the workspace is clear, the robot executes its pre-programmed tasks, such as pick-and-place operations, which are defined in the RoboDK simulation environment.

5.  **RoboDK Driver for KUKA**
    The system utilizes the RoboDK driver to translate the motion commands generated in RoboDK into a format that the KUKA robot controller can understand and execute. This driver facilitates communication, ensuring accurate execution of pick-and-place commands.

6.  **KUKA Robot (Execution)**
    The KUKA robot receives the motion commands from RoboDK and performs the physical assembly tasks. It follows precise instructions, often guided by a file like `RoboDKSynch.src`, which ensures synchronized actions.

## System Integration

### Requirements

To set up and run the system, ensure the following software and hardware components are available:

* **RoboDK Software:** Required for robot simulation and offline programming.
* **KUKA Robot:** The robot must be connected to the RoboDK system for task execution.
* **Camera:** A camera placed in the workspace to capture real-time video.
* **OpenCV:** Used for processing the video feed and human segmentation.
* **YOLOv8s-seg:** Pretrained model for real-time human segmentation in video.
* **Python:** The system uses Python for processing, controlling the robot through the RoboDK API, and managing communication between components.

### Installation

1.  **Install RoboDK:**
    * Download and install RoboDK from the official website: [RoboDK Download](https://robodk.com/download).
    
2.  **Install Python Libraries:**
    * Install the necessary Python libraries using pip:
        ```bash
        pip install opencv-python numpy robodk
        ```

3.  **Set Up Camera:**
    * Connect a camera to your system and configure it to capture video feeds.
    * Position the camera to cover the entire workspace, including the robot's operational area.

4.  **Download YOLOv8s-seg Model:**
    * Download the pretrained YOLOv8s-seg model weights (e.g., `yolov8s-seg.pt`). You might need to refer to the YOLOv8 documentation for the download instructions.
    * Implement the model using OpenCV and a deep learning framework like PyTorch or TensorFlow for real-time human segmentation in your Python script.

5.  **Integrate RoboDK with KUKA:**
    To connect RoboDK to your KUKA robot, you typically need to configure a communication channel. One common method involves using the KUKA VarProxy server. Follow these steps on your **KUKA robot controller (HMI)**:

    a.  **Enable Administrator Rights:**
        `KUKA` → `Configuration` → `User group` → Choose `Administrator`

    b.  **Minimize HMI:**
        `KUKA` → `Start-up` → `Service` → `Minimize HMI` (This will show the Windows desktop of the robot controller).

    c.  **Copy KUKAVARPROXY:**
        Copy the `KUKAVARPROXY` folder to the Desktop (or another accessible location on the robot controller).

    d.  **Unlock Port 7000:**
        This step configures the firewall on the robot controller to allow communication on the necessary port.
        i.   Select the HMI.
        ii.  `KUKA` → `Start-up` → `Network configuration` → `Advanced`
        iii. `NAT` → `Add port` → `Port number` `7000`
        iv.  Set permitted protocols: `tcp/udp`

    e.  **Start KUKAVARPROXY:**
        Run the `KUKAVARPROXY.EXE` program located in the copied `KUKAVARPROXY` folder on the robot controller.

    f.  **(Optional) Autostart KUKAVARPROXY:**
        To ensure the server starts automatically on reboot (recommended):
        i.   Create a shortcut of the `KUKAVARPROXY.EXE` file.
        ii.  Select `Windows START` → `All programs` → Right-click `startup` → `Open`.
        iii. Paste the shortcut into the startup folder.

    The `KUKAVARPROXY` server is now running on your KUKA robot controller, allowing the exchange of global variables with the remote PC running RoboDK.

    g.  **Configure Global Variables:**
        To enable communication of robot actions, you need to declare specific global variables in the KUKA controller's configuration file.
        Copy the `$config.dat` file here `KRC\R1\` and `KRC\R1\STEU\`.
    h.  **Copy Main Communication Program:**
        Copy the program `RoboDKSync35.src` into the `KRC\R1\` folder on the KUKA controller.

    i.  **Start RoboDK Synchronization Program:**
        You can now manually start the `RoboDKSync35.src` program on the KUKA controller to enable motion control from RoboDK. Alternatively, you can initiate this program from the command line (refer to RoboDK documentation for details). Even if this program isn't actively running, RoboDK can still read the robot's joint values as long as the `KUKAVARPROXY` program is running.

### Integration Flow

1.  The camera captures the live video feed of the workspace.
2.  The YOLOv8s-seg model processes this feed to detect and segment humans.
3.  The system checks if any detected humans are within the predefined danger zone.
4.  **If a human is detected in the danger zone:**
    * The Python script, using the RoboDK API, sends a command to the KUKA robot to stop its current motion. This communication happens through the configured connection (e.g., using the KUKA VarProxy).
    * A warning mechanism (e.g., a visual or auditory alert) is triggered.
5.  **If the workspace is clear of humans:**
    * The Python script, using the RoboDK API, instructs the KUKA robot to continue its pre-programmed assembly tasks by sending motion commands. These commands are based on the RoboDK project and are translated by the RoboDK driver.

## How to Use

1.  **Run the System:**
    * Execute the Python script that manages the camera feed, performs human detection using YOLOv8s-seg, determines if a human is in the danger zone, and controls the robot's operation via the RoboDK API.
    * The script will continuously monitor the workspace and react to human presence in the danger zone.

2.  **Monitor the Robot’s Operations:**
    * Observe the KUKA robot performing its programmed tasks. If a human enters the defined danger zone, the robot will automatically cease its movement.
    * Once the danger zone is clear and the Python script detects this, the robot will resume its operation.

3.  **Adjust the Danger Zone:**
    * Modify the parameters in your Python code that define the boundaries of the danger zone to customize the safety area around the robot according to your specific workspace and safety requirements.

4.  **Customize Assembly Tasks:**
    * Use the RoboDK software to create and modify the pick-and-place tasks or other assembly operations that the robot will perform. Ensure that the Python script is configured to send the appropriate RoboDK commands to the robot.

## Future Enhancements

* **Improved Human Detection:** Integrate more advanced human pose estimation techniques to enhance the accuracy and reliability of human detection and tracking.
* **Advanced Robot Behavior:** Implement more sophisticated robot behaviors, such as collaborative modes where the robot can work safely alongside humans or dynamic re-planning of tasks based on human presence.
* **Multi-Robot Integration:** Extend the system to manage multiple robots operating in the same workspace, ensuring collision avoidance between robots and with humans.

## Troubleshooting

* **Camera Not Working:**
    * Ensure the camera is properly connected to the system and that the necessary drivers are installed.
    * Verify the camera's resolution and frame rate settings in your Python script.

* **Robot Not Stopping:**
    * Double-check the communication setup between RoboDK and the KUKA robot controller (e.g., verify that KUKAVARPROXY is running and the IP address and port are correctly configured in your Python script and RoboDK).
    * Ensure that the RoboDK API functions for stopping the robot are correctly implemented in your Python code and that the `COM_ACTION` variable on the KUKA controller is being appropriately set.

* **Robot Not Resuming:**
    * Verify the logic in your Python script that checks for the clearance of the danger zone and sends the resume command to the robot via the RoboDK API. Ensure that the `COM_ACTION` and potentially the motion program on the KUKA controller are correctly managed for resumption.
