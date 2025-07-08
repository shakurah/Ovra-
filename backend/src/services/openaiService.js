const OpenAI = require('openai');

class OpenAIService {
  constructor() {
    this.client = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY,
    });
  }

  async enhanceSearchQuery(userQuery) {
    try {
      const messages = [
        {
          role: 'system',
          content: 'You are an expert in Spanish legal terminology and BOE (Boletín Oficial del Estado) search optimization. Given a user query, generate 2-3 improved search terms that would be most effective for searching official Spanish legal documents. Focus on: 1) Legal terminology, 2) Official document keywords, 3) Specific regulatory terms. Return ONLY a valid JSON object with the format: {"query1":"term1","query2":"term2","query3":"term3"}. No explanations, no markdown, just the JSON.'
        },
        {
          role: 'user',
          content: `User query: "${userQuery}"\n\nGenerate optimized BOE search terms in JSON format:`
        }
      ];

      const completion = await this.client.chat.completions.create({
        model: 'gpt-4o',
        messages: messages,
        max_tokens: 200,
        temperature: 0.3,
      });

      const jsonResponse = completion.choices[0].message.content.trim();
      
      try {
        const parsedQueries = JSON.parse(jsonResponse);
        const queryValues = Object.values(parsedQueries).filter(query => query && query.trim().length > 0);
        return queryValues.length > 0 ? queryValues : [userQuery];
      } catch (parseError) {
        console.error('Error parsing JSON response:', parseError);
        return [userQuery];
      }
    } catch (error) {
      console.error('Error enhancing search query:', error);
      // Fallback to original query if enhancement fails
      return [userQuery];
    }
  }

  async generateResponse(question, conversationHistory = [], boeResults = null) {
    try {
      // Prepare context from conversation history
      const messages = [
        {
          role: 'system',
          content: `Eres un asistente fiscal especializado en la legislación española. Tu trabajo es ayudar a profesionales culturales con preguntas sobre impuestos, facturación y regulaciones fiscales en España.

Instrucciones:
1. Responde SOLO en español
2. Sé preciso y cita la legislación relevante cuando sea posible
3. Si tienes información del BOE, úsala para dar respuestas más precisas
4. Mantén un tono profesional pero amigable
5. Si no tienes información suficiente, indica que recomiendas consultar con un profesional

Información del BOE disponible: ${boeResults && boeResults.length > 0 ? 'Sí' : 'No'}`
        }
      ];

      // Add conversation history
      if (conversationHistory && conversationHistory.length > 0) {
        conversationHistory.forEach(msg => {
          messages.push({
            role: msg.role,
            content: msg.content
          });
        });
      }

      // Add BOE context if available
      if (boeResults && boeResults.length > 0) {
        const boeContext = boeResults.slice(0, 3).map(result => `- ${result.title}: ${result.content}`).join('\n');
        messages.push({
          role: 'system',
          content: `Información relevante del BOE:\n${boeContext}`
        });
      }

      // Add current question
      messages.push({
        role: 'user',
        content: question
      });

      const completion = await this.client.chat.completions.create({
        model: 'gpt-4o',
        messages: messages,
        max_tokens: 1000,
        temperature: 0.3,
      });

      const answer = completion.choices[0].message.content.trim();
      
      // Extract citations if BOE results were used
      const citations = boeResults && boeResults.length > 0 ? 
        boeResults.slice(0, 3).map(result => ({
          article: result.title,
          law: result.source || 'BOE',
          url: result.url
        })) : [];

      return {
        answer,
        citations,
        sources: boeResults || []
      };
    } catch (error) {
      console.error('Error generating response:', error);
      return {
        answer: 'Lo siento, ha ocurrido un error al generar la respuesta. Por favor, inténtalo de nuevo.',
        citations: [],
        sources: []
      };
    }
  }

  async processMessage(message, boeResults = null) {
    
    try {
      // Validate and prepare BOE results
      const trimmedBoeResults = boeResults ? boeResults.slice(0, 2000) : '';
      const hasValidResults = boeResults && boeResults.length > 0;
      
      // Log for debugging
      console.log('BOE Results received:', hasValidResults ? 'Yes' : 'No');
      if (hasValidResults) {
        console.log('BOE Results length:', boeResults.length);
      }
      const messages = [
        {
          role: 'system',
          content: `INSTRUCCIONES CRÍTICAS: DEBES incluir SIEMPRE las referencias legales de los resultados de búsqueda del BOE en tu respuesta.

## RESULTADOS DE BÚSQUEDA DEL BOE:
${trimmedBoeResults}

## INSTRUCCIONES DETALLADAS:
1. RESPONDE SIEMPRE EN ESPAÑOL
2. Eres un asistente especializado en documentos legales y oficiales españoles
3. OBLIGATORIO: Analiza los resultados de búsqueda del BOE proporcionados arriba
4. OBLIGATORIO: Incluye TODAS las referencias legales relevantes encontradas en los resultados
5. OBLIGATORIO: Ordena las referencias de la más reciente a la más antigua

## FORMATO OBLIGATORIO DE REFERENCIAS:
Para cada referencia legal encontrada en los resultados de búsqueda, usa exactamente este formato:

### 📜 REFERENCIAS LEGALES ENCONTRADAS:

**[Título completo del documento]**
- **BOE Número:** [Número]
- **Fecha de publicación:** [Fecha]
- **Enlace:** [URL si está disponible]
- **Relevancia:** [Breve explicación de por qué es relevante]

---

## ESTRUCTURA DE RESPUESTA OBLIGATORIA:
1. **Respuesta directa a la consulta**
2. **Análisis basado en los resultados de búsqueda**
3. **Referencias legales formateadas (sección obligatoria)**
4. **Conclusiones y recomendaciones**

Si NO encuentras resultados específicos en los datos proporcionados, indica claramente que no se encontraron resultados relevantes en la búsqueda actual, pero proporciona conocimiento legal general.`
        }
      ];

      if (hasValidResults) {
        messages.push({
          role: 'system',
          content: `DATOS DE BÚSQUEDA ADICIONALES: Los siguientes resultados han sido encontrados y DEBEN ser incluidos en la respuesta:

${JSON.stringify(boeResults, null, 2)}`
        });
      }

      messages.push({
        role: 'user',
        content: message
      });

      const completion = await this.client.chat.completions.create({
        model: 'gpt-4o',
        messages: messages,
        max_tokens: 2000,
        temperature: 0.7,
      });

      return completion.choices[0].message.content;
    } catch (error) {
      console.error('Error processing message with OpenAI:', error);
      throw error;
    }
  }

  async *streamMessage(message, boeResults = null) {
    try {
      // Validate and prepare BOE results
      const trimmedBoeResults = boeResults ? boeResults.slice(0, 2000) : '';
      const hasValidResults = boeResults && boeResults.length > 0;
      
      // Log for debugging
      console.log('BOE Results received:', hasValidResults ? 'Yes' : 'No');
      if (hasValidResults) {
        console.log('BOE Results length:', boeResults.length);
      }
      const messages = [
        {
          role: 'system',
          content: `INSTRUCCIONES CRÍTICAS: DEBES incluir SIEMPRE las referencias legales de los resultados de búsqueda del BOE en tu respuesta.

## RESULTADOS DE BÚSQUEDA DEL BOE:
${trimmedBoeResults}

## INSTRUCCIONES DETALLADAS:
1. RESPONDE SIEMPRE EN ESPAÑOL
2. Eres un asistente especializado en documentos legales y oficiales españoles
3. OBLIGATORIO: Analiza los resultados de búsqueda del BOE proporcionados arriba
4. OBLIGATORIO: Incluye TODAS las referencias legales relevantes encontradas en los resultados
5. OBLIGATORIO: Ordena las referencias de la más reciente a la más antigua

## FORMATO OBLIGATORIO DE REFERENCIAS:
Para cada referencia legal encontrada en los resultados de búsqueda, usa exactamente este formato:

### 📜 REFERENCIAS LEGALES ENCONTRADAS:

**[Título completo del documento]**
- **BOE Número:** [Número]
- **Fecha de publicación:** [Fecha]
- **Enlace:** [URL si está disponible]
- **Relevancia:** [Breve explicación de por qué es relevante]

---

## ESTRUCTURA DE RESPUESTA OBLIGATORIA:
1. **Respuesta directa a la consulta**
2. **Análisis basado en los resultados de búsqueda**
3. **Referencias legales formateadas (sección obligatoria)**
4. **Conclusiones y recomendaciones**

Si NO encuentras resultados específicos en los datos proporcionados, indica claramente que no se encontraron resultados relevantes en la búsqueda actual, pero proporciona conocimiento legal general.`
        }
      ];

      if (hasValidResults) {
        messages.push({
          role: 'system',
          content: `DATOS DE BÚSQUEDA ADICIONALES: Los siguientes resultados han sido encontrados y DEBEN ser incluidos en la respuesta:

${JSON.stringify(boeResults, null, 2)}`
        });
      }

      messages.push({
        role: 'user',
        content: message
      });

      const stream = await this.client.chat.completions.create({
        model: 'gpt-4o',
        messages: messages,
        max_tokens: 2000,
        temperature: 0.7,
        stream: true,
      });

      for await (const chunk of stream) {
        const content = chunk.choices[0]?.delta?.content;
        if (content) {
          yield content;
        }
      }
    } catch (error) {
      console.error('Error streaming message with OpenAI:', error);
      throw error;
    }
  }
}

module.exports = new OpenAIService();