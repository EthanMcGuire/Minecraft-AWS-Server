const AWS = require('aws-sdk');
const ec2 = new AWS.EC2();

exports.handler = async (event) => {
    let instanceId = process.env.INSTANCE_ID;
    let onUrl = process.env.ON_URL;
    let offUrl = process.env.OFF_URL;

    // Check the current state of the instance
    const params = {
        InstanceIds: [instanceId],
    };
    const data = await ec2.describeInstances(params).promise();
    const state = data.Reservations[0].Instances[0].State.Name;

    const response = {
        statusCode: 200,
        headers: {
            'Content-Type': 'text/html',
        },
        body: `
        <html>
          <head>
            <meta charset="UTF-8">
            <title>Minecraft Server Control</title>
          </head>
          <body>
            <h1>Minecraft Server Status</h1>
              <p>Server State: ${state}</p>
              ${
                state === 'stopped'
                  ? '<button onclick="startInstance()">Start Instance</button>'
                  : '<button onclick="stopInstance()">Stop Instance</button>'
              }
              <script>
              function startInstance() {
                fetch('${onUrl}')
                  .then(response => response.text())
                  .then(html => document.getElementById('content').innerHTML = html)
                  .catch(error => console.error(error));
                  alert('Starting instance...');
              }
              function stopInstance() {
                fetch('${offUrl}')
                  .then(response => response.text())
                  .then(html => document.getElementById('content').innerHTML = html)
                  .catch(error => console.error(error));
                  alert('Stopping instance...');
              }
              </script>
          </body>
        </html>
      `,
    };

    return response;
};
