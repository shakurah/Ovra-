const { PrismaClient } = require('@prisma/client');
const bcrypt = require('bcryptjs');

const prisma = new PrismaClient();

async function createSuperuser() {
  try {
    const email = 'admin@ovra.ai';
    const password = 'admin123';
    
    // Check if superuser already exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });
    
    if (existingUser) {
      console.log('Superuser already exists with email:', email);
      return;
    }
    
    // Hash password
    const saltRounds = 10;
    const passwordHash = await bcrypt.hash(password, saltRounds);
    
    // Create superuser
    const superuser = await prisma.user.create({
      data: {
        email,
        passwordHash,
        firstName: 'Admin',
        lastName: 'User',
        isActive: true,
        isSuperuser: true,
      }
    });
    
    console.log('Superuser created successfully!');
    console.log('Email:', email);
    console.log('Password:', password);
    console.log('User ID:', superuser.id);
    console.log('\nYou can now login to the admin panel at: http://localhost:8000/admin');
    
  } catch (error) {
    console.error('Error creating superuser:', error);
  } finally {
    await prisma.$disconnect();
  }
}

createSuperuser();