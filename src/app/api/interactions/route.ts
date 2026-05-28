export async function handler(request: Request) {
  const data = await request.json();

  interface ResponseChoice {
    message?: { content?: string };
    text?: string;
  }

  const choices: Array<ResponseChoice> = data.choices || [];

  // Assuming the logic uses choices here, example:
  if (!choices.length) {
    throw new Error('No data available in response');
  }

  return {
    status: 200,
    body: choices,
  };
}
