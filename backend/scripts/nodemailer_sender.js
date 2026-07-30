const nodemailer = require('nodemailer');

async function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

async function main() {
  try {
    const raw = await readStdin();
    const payload = JSON.parse(raw || '{}');

    if (!payload.transport || !payload.message) {
      throw new Error('Missing transport or message in payload');
    }

    const transporter = nodemailer.createTransport(payload.transport);
    const info = await transporter.sendMail(payload.message);

    process.stdout.write(JSON.stringify({
      ok: true,
      messageId: info.messageId,
      accepted: info.accepted || [],
      rejected: info.rejected || []
    }));
  } catch (error) {
    process.stderr.write(
      JSON.stringify({
        ok: false,
        error: error && error.message ? error.message : String(error)
      })
    );
    process.exit(1);
  }
}

main();
